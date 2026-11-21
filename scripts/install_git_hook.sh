#!/usr/bin/env bash
# Install a git pre-commit hook that blocks commits containing PDK/foundry
# content or private data (license servers, IPs, e-mails, home paths, keys).
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
hook="$root/.git/hooks/pre-commit"
cat > "$hook" <<'HOOK'
#!/usr/bin/env bash
# pre-commit: scan the repository before every commit
root="$(git rev-parse --show-toplevel)"
if ! python3 "$root/tools/check_no_pdk.py" "$root"; then
  echo ""
  echo "Commit blocked by tools/check_no_pdk.py (see SECURITY.md)."
  echo "Fix the findings, or mark a reviewed line with 'pdk-check: allow'."
  exit 1
fi
HOOK
chmod +x "$hook"
echo "Installed pre-commit hook: $hook"
