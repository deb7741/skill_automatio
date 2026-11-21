#!/usr/bin/env bash
# Run sweeps + Monte Carlo, then summarize bandwidth of every AC result file.
set -euo pipefail
cd "$(dirname "$0")"
command -v spectre >/dev/null || { echo "spectre not on PATH"; exit 1; }

rm -rf psf
spectre sweeps_mc.scs +escchars =log spectre.log -format psfascii -raw psf "$@"

if command -v python3 >/dev/null; then
  echo "file,bw_hz"
  for f in psf/*.ac; do
    bw=$(python3 ../../python/read_psf.py "$f" --bandwidth out --quiet || echo "nan")
    echo "$(basename "$f"),$bw"
  done
fi
