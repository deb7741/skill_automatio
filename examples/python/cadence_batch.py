#!/usr/bin/env python3
"""Run Ocean, SKILL or ADE Assembler (maestro) jobs in batch and collect results.

Sub-commands
------------
  ocean   <script.ocn>                    run 'ocean -nograph -restore', collect OCEAN_RESULT lines
  skill   <script.il>                     run 'virtuoso -nograph -restore', check BATCH_STATUS
  maestro --lib L --cell C [--var k=v]    run examples/skill/run_maestro.il via env vars

Examples
--------
  cadence_batch.py ocean ../ocean/01_basic_tran_ac.ocn --json result.json
  cadence_batch.py skill ../skill/batch_wrapper.il --env VAG_LIB=scratchLib
  cadence_batch.py maestro --lib myLib --cell myTb --var rval=2k --csv out/myTb.csv

Scripts communicate with this driver through marker lines on stdout:
  OCEAN_RESULT key=value key=value ...
  BATCH_STATUS: PASS|FAIL
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

HERE = Path(__file__).resolve().parent
SKILL_DIR = (HERE / ".." / "skill").resolve()

_RESULT_RE = re.compile(r"^OCEAN_RESULT\s+(.*)$")
_KV_RE = re.compile(r"(\w+)=(\S+)")
_STATUS_RE = re.compile(r"BATCH_STATUS:\s*(PASS|FAIL)")


def parse_ocean_results(text: str) -> Dict[str, object]:
    """Collect key=value pairs from all OCEAN_RESULT lines (numbers converted)."""
    out: Dict[str, object] = {}
    for line in text.splitlines():
        m = _RESULT_RE.match(line.strip())
        if not m:
            continue
        for k, v in _KV_RE.findall(m.group(1)):
            try:
                out[k] = float(v)
            except ValueError:
                out[k] = v
    return out


def parse_batch_status(text: str) -> Optional[bool]:
    """True/False from the last BATCH_STATUS marker, None if absent."""
    found = _STATUS_RE.findall(text)
    return None if not found else found[-1] == "PASS"


def _run(cmd: List[str], env_extra: Dict[str, str], log: Path, cwd: Path, timeout: float) -> str:
    env = dict(os.environ, **env_extra)
    print("running:", " ".join(cmd), f"(cwd={cwd})")
    try:
        proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
        text = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        text = "\nTIMEOUT after %.0f s\nBATCH_STATUS: FAIL\n" % timeout
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(text)
    return text


def _env_pairs(items: List[str]) -> Dict[str, str]:
    env = {}
    for item in items:
        k, _, v = item.partition("=")
        env[k] = v
    return env


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--env", action="append", default=[], help="NAME=value for the job")
    common.add_argument("--log", default=None, help="log file (default: logs/<name>.log)")
    common.add_argument("--timeout", type=float, default=7200)
    common.add_argument("--json", help="write collected results to JSON")

    p_oc = sub.add_parser("ocean", parents=[common])
    p_oc.add_argument("script")
    p_sk = sub.add_parser("skill", parents=[common])
    p_sk.add_argument("script")
    p_sk.add_argument("--nocdsinit", action="store_true")
    p_ma = sub.add_parser("maestro", parents=[common])
    p_ma.add_argument("--lib", required=True)
    p_ma.add_argument("--cell", required=True)
    p_ma.add_argument("--var", action="append", default=[], help="design variable name=value")
    p_ma.add_argument("--csv", help="export results CSV here")
    p_ma.add_argument("--run-mode", help='e.g. "Single Run, Sweeps and Corners"')
    args = ap.parse_args(argv)

    env = _env_pairs(args.env)
    cwd = Path.cwd()

    if args.cmd == "ocean":
        script = Path(args.script).resolve()
        exe = "ocean"
        cmd = [exe, "-nograph", "-restore", script.name]
        cwd = script.parent
        name = script.stem
    elif args.cmd == "skill":
        script = Path(args.script).resolve()
        exe = "virtuoso"
        cmd = [exe, "-nograph"] + (["-nocdsinit"] if args.nocdsinit else []) + ["-restore", str(script)]
        env.setdefault("VAG_SKILL_DIR", str(SKILL_DIR))
        name = script.stem
    else:
        exe = "virtuoso"
        cmd = [exe, "-nograph", "-restore", str(SKILL_DIR / "run_maestro.il")]
        env.update(VAG_SKILL_DIR=str(SKILL_DIR), VAG_LIB=args.lib, VAG_CELL=args.cell)
        if args.var:
            env["VAG_VARS"] = ",".join(args.var)
        if args.csv:
            env["VAG_CSV"] = str(Path(args.csv).resolve())
        if args.run_mode:
            env["VAG_RUNMODE"] = args.run_mode
        name = f"maestro_{args.lib}_{args.cell}"

    if shutil.which(exe) is None:
        print(f"error: {exe!r} not on PATH (source your Cadence setup script)", file=sys.stderr)
        return 2

    log = Path(args.log) if args.log else Path("logs") / f"{name}.log"
    if args.cmd != "ocean":
        cmd += ["-log", str(log.with_suffix(".cds.log").resolve())]
    text = _run(cmd, env, log.resolve(), cwd, args.timeout)

    result: Dict[str, object] = {"job": name, "log": str(log)}
    if args.cmd == "ocean":
        result["results"] = parse_ocean_results(text)
        ok = bool(result["results"])
    else:
        status = parse_batch_status(text)
        result["batch_status"] = status
        ok = bool(status)
    result["passed"] = ok

    print(json.dumps(result, indent=2))
    if args.json:
        Path(args.json).write_text(json.dumps(result, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
