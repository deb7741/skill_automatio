#!/usr/bin/env python3
"""Summarize one or more Spectre logs; exit 1 if any failed.

  parse_spectre_log.py spectre.log
  parse_spectre_log.py runs/*/spectre.log --json summary.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from vautil.logparse import parse_spectre_log  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("logs", nargs="+", help="Spectre log files")
    ap.add_argument("--json", metavar="FILE", help="write all results as JSON")
    ap.add_argument("--show-warnings", action="store_true")
    args = ap.parse_args(argv)

    results = [parse_spectre_log(p) for p in args.logs]
    for r in results:
        status = "PASS" if r.passed else ("INCOMPLETE" if not r.completed else "FAIL")
        summ = r.summary or {"errors": len(r.errors), "warnings": len(r.warnings), "notices": r.notices}
        t = sum(r.analysis_times_s.values())
        print(f"{status:<10} {r.path}  errors={summ['errors']} warnings={summ['warnings']} "
              f"analysis_time={t:.3g}s")
        for e in r.errors:
            print(f"    ERROR   {e}")
        for f in r.fatal_lines:
            print(f"    FATAL   {f}")
        if args.show_warnings:
            for w in r.warnings:
                print(f"    WARNING {w}")

    if args.json:
        Path(args.json).write_text(json.dumps([r.to_dict() for r in results], indent=2))
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
