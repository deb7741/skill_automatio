#!/usr/bin/env bash
# Single-step AMS Designer run: SystemVerilog testbench + Spectre/Verilog-A block.
# Usage: ./run.sh [aps|x|fx]      (analog engine, default: aps)
set -euo pipefail
cd "$(dirname "$0")"
command -v xrun >/dev/null    || { echo "xrun not on PATH"; exit 1; }
command -v spectre >/dev/null || { echo "spectre not on PATH (needed by AMS)"; exit 1; }

case "${1:-aps}" in
  aps) SPECTRE_ARGS="+aps" ;;
  x)   SPECTRE_ARGS="+preset=mx +mt=4" ;;
  fx)  SPECTRE_ARGS="+fx +spectre +preset=lx +mt=4" ;;
  *)   echo "unknown engine $1"; exit 2 ;;
esac

xrun -clean \
     -timescale 1ns/1ps \
     ./tb_dac.sv \
     ./amscf.scs \
     -access +r \
     -iereport \
     -spectre_args "$SPECTRE_ARGS" \
     -input probe.tcl \
     -l xrun_ams.log

grep -E "TEST (PASSED|FAILED)" xrun_ams.log || echo "No PASS/FAIL banner; inspect xrun_ams.log"
echo "IE report: look for the interface-element section in xrun_ams.log / the AMS log files"
