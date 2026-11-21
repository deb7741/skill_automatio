# Contributing

Thanks for helping make Cadence automation less painful.

## The one hard rule

**No PDK, foundry, NDA-covered or private content** (license servers, host names, IPs, personal paths, logs from real projects). Read [DISCLAIMER.md](DISCLAIMER.md) and [SECURITY.md](SECURITY.md). Before you open a pull request, run:

```bash
python tools/check_no_pdk.py .
```

CI runs the same check and will fail the PR if it finds a blocked term. If you get a false positive (for example a word that happens to match), add it to the allow-list in `tools/check_no_pdk.py` and explain why in the PR.

## What makes a good contribution

- **A recipe that solves a real, common problem**, e.g. "export all Assembler outputs to CSV after every run"
- **A fix for a version difference**: say which release you tested (e.g. `IC6.1.8 ISR30`, `IC23.1 ISR12`, `SPECTRE 21.1`, `XCELIUM 23.09`)
- **A clearer explanation** of something that confused you
- **Tests** for Python helpers (use small fixture files, never real design data)

## Style

### Docs (Markdown)
- One topic per chapter, short sections, runnable snippets
- Use placeholders: `/path/to/...`, `myLib`, `myCell`, `<your-license-server>`
- Mark version-specific behavior: `> **IC23.1+:** ...`
- Write in your own words; link to the official manual instead of copying it

### SKILL
- Prefix all global functions and variables with a project prefix. This repo uses `vag` (Virtuoso Automation Guide), e.g. `vagListCells()`
- Keep variables local with `let()` or `prog()`
- Use `printf`/`warn`/`error` consistently; return `nil` on failure
- Header comment: purpose, usage, tested release

### Ocean
- Start scripts with `simulator('spectre)` and end batch scripts with `exit()`
- Put all user-editable settings at the top

### Python
- Python 3.8+, standard library first; optional deps in `requirements.txt`
- `argparse` CLI + importable functions
- Format with `black`, check with `ruff` or `flake8` if you have them

### Shell
- `#!/usr/bin/env bash` with `set -euo pipefail`
- Must pass `shellcheck`

## Pull request checklist

- [ ] No PDK/foundry/NDA content and no private data (`tools/check_no_pdk.py` passes)
- [ ] Release(s) you tested with are stated
- [ ] New Python code has tests, and `pytest` passes
- [ ] Shell scripts pass `shellcheck`
- [ ] Docs updated (and `docs/README.md` index if you added a chapter)
