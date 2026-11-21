#!/usr/bin/env bash
# Print versions of the Cadence tools on PATH and whether licenses are reachable.
# Run at the start of CI jobs so logs record exactly which versions were used.
#
# Privacy: by default prints NO host names, install paths or license-server
# names, so the output is safe to paste into issues or keep in shared logs.
# Use --paths to also show install locations (internal debugging only).
set -uo pipefail

show_paths=0
[[ "${1:-}" == "--paths" ]] && show_paths=1

ver() {
  local tool="$1"; shift
  if command -v "$tool" >/dev/null 2>&1; then
    local where=""
    [[ $show_paths -eq 1 ]] && where="$(command -v "$tool")"
    printf "%-10s %s %s\n" "$tool" "$("$tool" "$@" 2>&1 | head -1)" "$where"
  else
    printf "%-10s %s\n" "$tool" "NOT FOUND"
  fi
}

echo "== tools =="
ver virtuoso -W
ver spectre  -W
ver xrun     -version
ver ocean    -W
ver python3  --version

echo "== licenses =="
lic="${CDS_LIC_FILE:-${LM_LICENSE_FILE:-}}"
if command -v lmstat >/dev/null 2>&1 && [[ -n "$lic" ]]; then
  up=$(lmstat -c "$lic" 2>&1 | grep -c "license server UP")
  down=$(lmstat -c "$lic" 2>&1 | grep -cE "license server DOWN|Cannot connect")
  echo "license servers up: $up, down/unreachable: $down"
else
  echo "lmstat not found or CDS_LIC_FILE/LM_LICENSE_FILE not set"
fi
