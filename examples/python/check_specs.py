#!/usr/bin/env python3
"""Check simulation results (CSV) against a JSON spec file.

Works with two CSV shapes:

* wide  : one row per run/corner, one column per measurement
          (e.g. summary.csv from spectre_sweep.py)
* long  : one row per measurement, with a name column and a value column
          (e.g. an ADE Assembler/maestro export; pick columns with
          --name-col / --value-col to match your release's export)

Spec file:
{
  "bw":      {"min": 100e3, "unit": "Hz"},
  "gain_db": {"min": 40, "max": 60},
  "tr_s":    {"max": "2u"}          # engineering suffixes allowed
}

  check_specs.py summary.csv specs.json --report report.md --junit specs.xml
  check_specs.py maestro.csv specs.json --name-col Output --value-col Nominal
Exit code: 0 all pass, 1 any fail/missing.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from vautil.junit import TestResult, write_junit  # noqa: E402
from vautil.units import format_si, parse_si  # noqa: E402


def load_specs(path: Path) -> Dict[str, dict]:
    raw = json.loads(path.read_text())
    specs = {}
    for name, s in raw.items():
        specs[name] = {
            "min": parse_si(s["min"]) if "min" in s else None,
            "max": parse_si(s["max"]) if "max" in s else None,
            "unit": s.get("unit", ""),
        }
        if specs[name]["min"] is None and specs[name]["max"] is None:
            raise ValueError(f"spec {name!r} needs min and/or max")
    return specs


def _to_float(v: str) -> Optional[float]:
    try:
        x = parse_si(v)
        return None if math.isnan(x) else x
    except (ValueError, TypeError):
        return None


def collect_values(csv_path: Path, spec_names: List[str], name_col: Optional[str],
                   value_col: Optional[str], label_cols: List[str]) -> List[dict]:
    """Return list of {"label": str, "metric": str, "value": float|None}."""
    with open(csv_path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        return []
    out = []
    if name_col:                                             # long format
        vcol = value_col or "value"
        for i, r in enumerate(rows):
            metric = (r.get(name_col) or "").strip()
            if metric in spec_names:
                label = " ".join(r.get(c, "") for c in label_cols) or f"row{i + 1}"
                out.append({"label": label, "metric": metric, "value": _to_float(r.get(vcol, ""))})
    else:                                                    # wide format
        label_cols = label_cols or [c for c in rows[0] if c not in spec_names
                                    and c not in ("status", "runtime_s")]
        for i, r in enumerate(rows):
            label = ", ".join(f"{c}={r[c]}" for c in label_cols if c in r) or f"row{i + 1}"
            for metric in spec_names:
                if metric in r:
                    out.append({"label": label, "metric": metric, "value": _to_float(r[metric])})
    return out


def judge(value: Optional[float], spec: dict) -> str:
    if value is None:
        return "MISSING"
    if spec["min"] is not None and value < spec["min"]:
        return "FAIL"
    if spec["max"] is not None and value > spec["max"]:
        return "FAIL"
    return "PASS"


def limits_text(spec: dict) -> str:
    lo = format_si(spec["min"]) if spec["min"] is not None else ""
    hi = format_si(spec["max"]) if spec["max"] is not None else ""
    return f"[{lo} .. {hi}] {spec['unit']}".strip()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("specs")
    ap.add_argument("--name-col", help="long format: column holding measurement names")
    ap.add_argument("--value-col", help="long format: column holding values")
    ap.add_argument("--label-cols", nargs="*", default=[], help="columns identifying a run/corner")
    ap.add_argument("--report", help="write Markdown report")
    ap.add_argument("--junit", help="write JUnit XML")
    args = ap.parse_args(argv)

    specs = load_specs(Path(args.specs))
    values = collect_values(Path(args.csv), list(specs), args.name_col, args.value_col, args.label_cols)

    checks = []
    for v in values:
        status = judge(v["value"], specs[v["metric"]])
        checks.append({**v, "status": status})
    seen = {v["metric"] for v in values}
    for metric in specs:
        if metric not in seen:
            checks.append({"label": "-", "metric": metric, "value": None, "status": "MISSING"})

    n_fail = sum(c["status"] != "PASS" for c in checks)
    lines = [f"# Spec check: {Path(args.csv).name}", "",
             f"**{len(checks) - n_fail}/{len(checks)} checks passed**", "",
             "| Status | Metric | Run / corner | Value | Limits |", "|---|---|---|---|---|"]
    for c in sorted(checks, key=lambda c: (c["status"] == "PASS", c["metric"], c["label"])):
        val = format_si(c["value"]) if c["value"] is not None else "—"
        icon = {"PASS": "✅", "FAIL": "❌", "MISSING": "⚠️"}[c["status"]]
        lines.append(f"| {icon} {c['status']} | {c['metric']} | {c['label']} | {val} | "
                     f"{limits_text(specs[c['metric']])} |")
    report = "\n".join(lines) + "\n"
    print(report)
    if args.report:
        Path(args.report).write_text(report)
    if args.junit:
        write_junit([TestResult(name=f"{c['metric']} @ {c['label']}", passed=c["status"] == "PASS",
                                message=f"{c['status']}: {c['value']} not in {limits_text(specs[c['metric']])}"
                                if c["status"] != "PASS" else "", classname="specs")
                     for c in checks], args.junit, suite_name="spec-check")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
