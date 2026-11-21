#!/usr/bin/env bash
# Run the RC low-pass example with Spectre and print the -3 dB bandwidth.
# Usage: ./run.sh [extra spectre args, e.g. +aps or +preset=mx]
set -euo pipefail
cd "$(dirname "$0")"

command -v spectre >/dev/null || { echo "spectre not on PATH (source your setup script)"; exit 1; }

rm -rf psf
# psfascii so the Python helpers can read results without extra libraries
spectre rc_lowpass.scs +escchars =log spectre.log -format psfascii -raw psf "$@"
echo "Spectre finished: results in ./psf, log in ./spectre.log"

# Optional post-processing (no license needed)
if command -v python3 >/dev/null; then
  python3 ../../python/read_psf.py psf/ac1.ac --bandwidth out || true
fi
