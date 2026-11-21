#!/usr/bin/env python3
"""Parallel Spectre parameter sweep driven from Python.

Renders a netlist template for every point of a parameter grid, runs Spectre
in parallel (one directory per point), checks each log, measures results and
writes a CSV summary (+ optional JUnit XML).

Template placeholders use Python string.Template syntax: ${rval}, ${cval}.

Example (uses the template next to this script):

  spectre_sweep.py templates/rc_lowpass.scs.tmpl \\
      --param rval=500,1k,2k,5k --param cval=1n,2n \\
      --measure bw:ac1.ac:out --jobs 4 --out runs/rc_sweep

  # render netlists only (no Spectre needed) — good for checking templates
  spectre_sweep.py templates/rc_lowpass.scs.tmpl --param rval=1k,2k --dry-run
"""

from __future__ import annotations

import argparse
import csv
import itertools
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from string import Template
from typing import Dict, List, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from vautil import measure  # noqa: E402
from vautil.junit import TestResult, write_junit  # noqa: E402
from vautil.logparse import parse_spectre_log  # noqa: E402
from vautil.psf_ascii import read_psf_ascii  # noqa: E402


# ------------------------------------------------------------------ helpers --

def parse_param_args(items: Sequence[str]) -> Dict[str, List[str]]:
    """['rval=1k,2k', 'cval=1n'] -> {'rval': ['1k','2k'], 'cval': ['1n']}"""
    grid: Dict[str, List[str]] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"--param expects name=v1,v2,...; got {item!r}")
        name, values = item.split("=", 1)
        vals = [v.strip() for v in values.split(",") if v.strip()]
        if not vals:
            raise ValueError(f"no values for parameter {name!r}")
        grid[name.strip()] = vals
    return grid


def expand_grid(grid: Dict[str, List[str]]) -> List[Dict[str, str]]:
    """Full-factorial expansion, deterministic order."""
    if not grid:
        return [{}]
    names = list(grid)
    return [dict(zip(names, combo)) for combo in itertools.product(*(grid[n] for n in names))]


def point_name(point: Dict[str, str]) -> str:
    if not point:
        return "nominal"
    safe = lambda s: "".join(c if c.isalnum() or c in ".-" else "_" for c in s)  # noqa: E731
    return "_".join(f"{k}-{safe(v)}" for k, v in point.items())


def render_netlist(template_text: str, point: Dict[str, str]) -> str:
    """Substitute ${name} placeholders; unknown placeholders raise KeyError."""
    return Template(template_text).substitute(point)


def parse_measure_args(items: Sequence[str]) -> List[Tuple[str, str, str, str]]:
    """'bw:ac1.ac:out' -> (label, file, signal, kind). kind from file suffix."""
    out = []
    for item in items:
        parts = item.split(":")
        if len(parts) != 3:
            raise ValueError(f"--measure expects label:file:signal; got {item!r}")
        label, fname, sig = parts
        kind = "bandwidth" if fname.endswith(".ac") else "rise" if fname.endswith(".tran") else "final"
        out.append((label, fname, sig, kind))
    return out


def do_measure(rawdir: Path, measures) -> Dict[str, float]:
    res: Dict[str, float] = {}
    for label, fname, sig, kind in measures:
        try:
            d = read_psf_ascii(rawdir / fname)
            y = d.signal(sig)
            if kind == "bandwidth":
                v = measure.bandwidth(d.sweep_values, y)
            elif kind == "rise":
                yr = [float(abs(a)) if isinstance(a, complex) else float(a) for a in y]
                v = measure.rise_time(d.sweep_values, yr, v_initial=min(yr), v_final=max(yr))
            else:
                v = abs(y[-1]) if isinstance(y[-1], complex) else float(y[-1])
            res[label] = float("nan") if v is None else float(v)
        except (OSError, KeyError, ValueError) as exc:
            print(f"  measure {label} failed in {rawdir}: {exc}", file=sys.stderr)
            res[label] = float("nan")
    return res


# ------------------------------------------------------------------- runner --

def run_point(spectre: str, netlist: Path, extra: Sequence[str], timeout: float):
    rundir = netlist.parent
    rawdir = rundir / "psf"
    log = rundir / "spectre.log"
    cmd = [spectre, netlist.name, "+escchars", "-format", "psfascii",
           "-raw", "psf", "=log", log.name, *extra]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, cwd=rundir, capture_output=True, text=True, timeout=timeout)
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        rc = -999
    return rc, time.time() - t0, rawdir, log


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("template", help="netlist template with ${param} placeholders")
    ap.add_argument("--param", action="append", default=[], help="name=v1,v2,... (repeatable)")
    ap.add_argument("--measure", action="append", default=[],
                    help="label:psf_file:signal  (.ac -> bandwidth, .tran -> rise time)")
    ap.add_argument("--out", default="runs/sweep", help="output directory")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 2,
                    help="parallel Spectre jobs (limit to your license count!)")
    ap.add_argument("--timeout", type=float, default=3600, help="seconds per run")
    ap.add_argument("--spectre", default="spectre", help="spectre executable")
    ap.add_argument("--spectre-args", default="", help='extra args, e.g. "+aps +mt=1"')
    ap.add_argument("--junit", help="write JUnit XML here")
    ap.add_argument("--dry-run", action="store_true", help="only render netlists")
    args = ap.parse_args(argv)

    template_text = Path(args.template).read_text()
    points = expand_grid(parse_param_args(args.param))
    measures = parse_measure_args(args.measure)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # Render every netlist first (fails fast on template errors)
    jobs = []
    for pt in points:
        rundir = out / point_name(pt)
        rundir.mkdir(parents=True, exist_ok=True)
        netlist = rundir / "input.scs"
        netlist.write_text(render_netlist(template_text, pt))
        jobs.append((pt, netlist))
    print(f"rendered {len(jobs)} netlists under {out}/")
    if args.dry_run:
        return 0

    if shutil.which(args.spectre) is None:
        print(f"error: {args.spectre!r} not found on PATH", file=sys.stderr)
        return 2

    extra = args.spectre_args.split()
    rows, junit = [], []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futs = {pool.submit(run_point, args.spectre, nl, extra, args.timeout): pt for pt, nl in jobs}
        for fut in as_completed(futs):
            pt = futs[fut]
            rc, dt, rawdir, logf = fut.result()
            log = parse_spectre_log(logf) if logf.exists() else None
            ok = rc == 0 and log is not None and log.passed
            meas = do_measure(rawdir, measures) if ok else {m[0]: float("nan") for m in measures}
            status = "PASS" if ok else ("TIMEOUT" if rc == -999 else "FAIL")
            print(f"{status:<7} {point_name(pt):<40} {dt:6.1f}s  " +
                  " ".join(f"{k}={v:.4g}" for k, v in meas.items()))
            rows.append({**pt, **meas, "status": status, "runtime_s": round(dt, 2)})
            junit.append(TestResult(name=point_name(pt), passed=ok, time_s=dt,
                                    message="" if ok else f"{status} (rc={rc})",
                                    output="\n".join(log.errors + log.fatal_lines) if log else ""))

    rows.sort(key=lambda r: [str(r.get(k)) for k in points[0]])
    summary = out / "summary.csv"
    fields = list(points[0]) + [m[0] for m in measures] + ["status", "runtime_s"]
    with open(summary, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"summary: {summary}")
    if args.junit:
        write_junit(junit, args.junit, suite_name="spectre-sweep")
    return 0 if all(r["status"] == "PASS" for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
