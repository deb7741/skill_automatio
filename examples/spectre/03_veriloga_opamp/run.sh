#!/usr/bin/env bash
# Simulate the Verilog-A opamp testbench. Expected: closed-loop gain ~ 20 dB,
# closed-loop bandwidth ~ GBW/10 = 1 MHz.
set -euo pipefail
cd "$(dirname "$0")"
command -v spectre >/dev/null || { echo "spectre not on PATH"; exit 1; }

rm -rf psf
spectre tb_opamp.scs +escchars =log spectre.log -format psfascii -raw psf "$@"

if command -v python3 >/dev/null; then
  python3 ../../python/read_psf.py psf/ac1.ac --bandwidth out || true
fi
