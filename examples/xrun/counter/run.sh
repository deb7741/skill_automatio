#!/usr/bin/env bash
# Usage:
#   ./run.sh                 # batch run, waves in waves.shm
#   ./run.sh gui             # SimVision GUI
#   ./run.sh cov             # with coverage collection
#   ./run.sh seeds 8         # build once, run 8 random seeds in parallel
set -euo pipefail
cd "$(dirname "$0")"
command -v xrun >/dev/null || { echo "xrun not on PATH"; exit 1; }

mode="${1:-batch}"
case "$mode" in
  batch)
    xrun -f files.f -access +r -input probe.tcl -l xrun.log ;;
  gui)
    xrun -f files.f -access +rwc -linedebug -gui -l xrun_gui.log ;;
  cov)
    xrun -f files.f -coverage all -covtest seed1 -covoverwrite -svseed 1 -l xrun_cov.log
    echo "Merge/report with: imc -execcmd \"load -run cov_work/scope/seed1; report -summary\"" ;;
  seeds)
    n="${2:-4}"
    xrun -f files.f -elaborate -snapshot tb_snap -l build.log
    for s in $(seq 1 "$n"); do
      xrun -R -snapshot tb_snap -svseed "$s" -l "run_seed$s.log" &
    done
    wait
    grep -H -E "TEST (PASSED|FAILED)" run_seed*.log ;;
  *)
    echo "unknown mode: $mode"; exit 2 ;;
esac

if [[ -f xrun.log ]]; then
  grep -E "TEST (PASSED|FAILED)" xrun.log || echo "No PASS/FAIL banner found"
fi
