#!/usr/bin/env bash
# Run an Ocean script in batch and keep a log.
# Usage: ./run_ocean.sh 01_basic_tran_ac.ocn
set -euo pipefail
cd "$(dirname "$0")"

script="${1:?usage: $0 <script.ocn>}"
command -v ocean >/dev/null || { echo "ocean not on PATH (source your setup script)"; exit 1; }

mkdir -p sim logs
log="logs/${script%.ocn}.log"
ocean -nograph -restore "$script" 2>&1 | tee "$log"

# Surface machine-readable results
grep -E '^OCEAN_RESULT' "$log" || echo "(no OCEAN_RESULT lines found; check $log)"
