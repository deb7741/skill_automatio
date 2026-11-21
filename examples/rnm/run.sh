#!/usr/bin/env bash
# Pure-digital real-number-model run (no Spectre, no analog license).
set -euo pipefail
cd "$(dirname "$0")"
command -v xrun >/dev/null || { echo "xrun not on PATH"; exit 1; }

xrun -sv -timescale 1ns/1ps rnm_models.sv tb_dac_rnm.sv -top tb_dac_rnm \
     -access +r -l xrun_rnm.log
grep -E "TEST (PASSED|FAILED)" xrun_rnm.log
