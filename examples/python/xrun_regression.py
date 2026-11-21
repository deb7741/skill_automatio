#!/usr/bin/env python3
"""Run a list of xrun tests in parallel, judge them from their logs, write JUnit.

Test list (JSON):
{
  "workdir": "../xrun/counter",            # where xrun runs (relative to this JSON file)
  "common_args": ["-f", "files.f", "-access", "+r"],
  "tests": [
    {"name": "seed1",  "args": ["-svseed", "1"]},
    {"name": "long",   "args": ["-svseed", "2", "+CYCLES=2000"], "timeout": 600},
    {"name": "smoke",  "args": [], "tags": ["smoke"]}
  ]
}

  xrun_regression.py tests.json --jobs 4 --junit out/junit.xml
  xrun_regression.py tests.json --tags smoke
  xrun_regression.py tests.json --dry-run          # print commands only

Each test gets its own output dir and its own xcelium.d (-xmlibdirname), so
parallel runs never share compiled libraries.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent))

from vautil.junit import TestResult, summary_line, write_junit  # noqa: E402
from vautil.logparse import parse_xrun_log  # noqa: E402


def load_tests(path: Path) -> dict:
    spec = json.loads(path.read_text())
    if "tests" not in spec or not isinstance(spec["tests"], list):
        raise ValueError("test list must contain a 'tests' array")
    names = [t["name"] for t in spec["tests"]]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        raise ValueError(f"duplicate test names: {sorted(dupes)}")
    spec.setdefault("common_args", [])
    spec.setdefault("workdir", ".")
    return spec


def select_tests(spec: dict, tags: List[str], names: List[str]) -> List[dict]:
    tests = spec["tests"]
    if names:
        tests = [t for t in tests if t["name"] in names]
    if tags:
        tests = [t for t in tests if set(tags) & set(t.get("tags", []))]
    return tests


def build_command(xrun: str, spec: dict, test: dict, outdir: Path) -> List[str]:
    return [xrun, *spec["common_args"], *test.get("args", []),
            "-xmlibdirname", str(outdir / "xcelium.d"),
            "-l", str(outdir / "xrun.log")]


def run_test(cmd: List[str], cwd: Path, timeout: float):
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return proc.returncode, time.time() - t0, False
    except subprocess.TimeoutExpired:
        return -1, time.time() - t0, True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("testlist", help="JSON test list")
    ap.add_argument("--jobs", type=int, default=4, help="parallel tests (mind licenses)")
    ap.add_argument("--out", default="regress_out", help="output root")
    ap.add_argument("--tags", nargs="*", default=[], help="only tests with any of these tags")
    ap.add_argument("--only", nargs="*", default=[], help="only these test names")
    ap.add_argument("--timeout", type=float, default=1800, help="default timeout per test (s)")
    ap.add_argument("--xrun", default="xrun")
    ap.add_argument("--junit", help="JUnit XML output path")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    listfile = Path(args.testlist).resolve()
    spec = load_tests(listfile)
    workdir = (listfile.parent / spec["workdir"]).resolve()
    tests = select_tests(spec, args.tags, args.only)
    if not tests:
        print("no tests selected")
        return 2
    out_root = Path(args.out).resolve()

    plan = []
    for t in tests:
        outdir = out_root / t["name"]
        plan.append((t, outdir, build_command(args.xrun, spec, t, outdir)))

    if args.dry_run:
        for t, _, cmd in plan:
            print(f"[{t['name']}] (cd {workdir} && {' '.join(cmd)})")
        return 0
    if shutil.which(args.xrun) is None:
        print(f"error: {args.xrun!r} not on PATH", file=sys.stderr)
        return 2

    results: List[TestResult] = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futs = {}
        for t, outdir, cmd in plan:
            outdir.mkdir(parents=True, exist_ok=True)
            futs[pool.submit(run_test, cmd, workdir, t.get("timeout", args.timeout))] = (t, outdir)
        for fut in as_completed(futs):
            t, outdir = futs[fut]
            rc, dt, timed_out = fut.result()
            logf = outdir / "xrun.log"
            log = parse_xrun_log(logf) if logf.exists() else None
            passed = (not timed_out) and log is not None and log.passed
            if timed_out:
                msg = "timeout"
            elif log is None:
                msg = f"no log (rc={rc})"
            elif not passed:
                msg = "; ".join(log.tool_errors[:3]) or f"banner={log.banner} uvm={log.uvm} rc={rc}"
            else:
                msg = ""
            print(f"{'PASS' if passed else 'FAIL':<5} {t['name']:<24} {dt:7.1f}s  {msg}")
            results.append(TestResult(name=t["name"], passed=passed, time_s=dt, message=msg,
                                      output=logf.read_text(errors='replace')[-4000:] if logf.exists() else "",
                                      classname="xrun"))

    print(summary_line(results, "xrun regression"))
    if args.junit:
        write_junit(results, args.junit, suite_name="xrun-regression")
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
