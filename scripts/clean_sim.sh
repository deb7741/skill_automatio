#!/usr/bin/env bash
# Remove simulation outputs below a directory (default: current dir).
# Dry run by default; pass --yes to actually delete.
set -euo pipefail

root="."
doit=0
for arg in "$@"; do
  case "$arg" in
    --yes) doit=1 ;;
    *)     root="$arg" ;;
  esac
done

patterns=(psf "*.raw" xcelium.d INCA_libs "*.shm" cov_work "*.ahdlSimDB" .ahdl_include sim logs regress_out runs)
args=()
for p in "${patterns[@]}"; do
  args+=(-name "$p" -o)
done
unset 'args[${#args[@]}-1]'

mapfile -t hits < <(find "$root" -type d \( "${args[@]}" \) -prune -print 2>/dev/null)
if [[ ${#hits[@]} -eq 0 ]]; then
  echo "nothing to clean under $root"; exit 0
fi
printf '%s\n' "${hits[@]}"
if [[ $doit -eq 1 ]]; then
  rm -rf -- "${hits[@]}"
  echo "deleted ${#hits[@]} directories"
else
  echo "(dry run: re-run with --yes to delete)"
fi
