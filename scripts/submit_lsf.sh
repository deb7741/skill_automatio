#!/usr/bin/env bash
# Submit a simulator command to LSF and wait for it (bsub -K).
# Usage: submit_lsf.sh [-q queue] [-n threads] [-m memMB] -- <command...>
#   submit_lsf.sh -n 4 -- spectre tb.scs +mt=4 =log tb.log -raw psf
# Adapt queue names / resource strings to your site.
set -euo pipefail

queue="${LSF_QUEUE:-normal}"
threads=1
mem=4000
while [[ $# -gt 0 ]]; do
  case "$1" in
    -q) queue="$2"; shift 2 ;;
    -n) threads="$2"; shift 2 ;;
    -m) mem="$2"; shift 2 ;;
    --) shift; break ;;
    *)  echo "unknown option $1"; exit 2 ;;
  esac
done
[[ $# -gt 0 ]] || { echo "no command given"; exit 2; }

mkdir -p lsf_logs
exec bsub -K -q "$queue" -n "$threads" \
     -R "span[hosts=1] rusage[mem=${mem}]" \
     -o "lsf_logs/%J.out" -e "lsf_logs/%J.err" \
     "$@"
