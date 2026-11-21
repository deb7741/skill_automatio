# Security & privacy

This repository is meant to be **public**. Anything committed here, including
anything in the git history, can be read by anyone, forever.

## Never commit

| Category | Examples |
|---|---|
| License details | `CDS_LIC_FILE` / `LM_LICENSE_FILE` values (`port@host`), license files (`*.dat`, `*.lic`), feature counts |
| Site / device details | Host names, IP addresses, install paths that reveal your company or user name (`/home/<you>`, `/tools/<corp>/...`), queue names |
| PDK / foundry data | Model files, corner contents, device names, tech files, layer maps, rule decks (see [DISCLAIMER.md](DISCLAIMER.md)) |
| Design data | Real netlists, schematics, simulation logs or results from real projects |
| Credentials | Passwords, SSH keys, API tokens, CI secrets |

The repo ships **templates only** (`*.template` with placeholders such as
`5280@license-server` and `/path/to/cadence/IC618`). Your filled-in copies
(`setup_env.sh`, `cds.lib`, `cds.lib.project`, `.cdsinit`, `.cdsenv`, `si.env`, ...)
are listed in `.gitignore`, so git won't pick them up by accident.

## Automatic checks

`tools/check_no_pdk.py` scans for foundry names, PDK-type files, license
servers, IP addresses, e-mail addresses, home-directory paths, private keys and
access tokens. It runs:

1. **In GitHub CI** on every push and pull request
2. **Locally before every commit**, if you install the hook (recommended):

   ```bash
   scripts/install_git_hook.sh
   ```

Run it manually at any time: `python3 tools/check_no_pdk.py .`

## Before you push, check yourself too

```bash
git status --ignored          # make sure private files are listed as ignored
git diff --cached             # read what you are about to commit
python3 tools/check_no_pdk.py .
```

Logs and screenshots are the most common leaks: they contain host names, user
names, paths and tool versions. Trim them to the relevant lines and replace
names with placeholders before sharing.

## If something leaked

1. **Assume it's public.** Bots scan new GitHub commits within minutes.
2. Rotate anything secret (tokens, passwords, keys) first.
3. Remove it from history, not just from the latest commit, e.g. with
   [`git filter-repo`](https://github.com/newren/git-filter-repo), then force-push.
4. Tell your CAD/IT or security team if license or company data was exposed.

## Reporting

If you find sensitive data in this repository, please open an issue that
**does not repeat the data** ("possible license info in file X"), or contact the
maintainer privately. It will be removed from the history.
