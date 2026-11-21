#!/usr/bin/env python3
"""Fail if the repository contains PDK/foundry content or private site/device data.

Checks:
  * foundry names and well-known PDK device identifiers
  * PDK-type files (tech files, layer maps, rule decks, ...)
  * private data: real license servers (port@host), IP addresses, e-mail
    addresses, home-directory paths (user names), private keys, API tokens

This is a safety net, not a guarantee: reviewers still need to look at what
gets committed. Run locally before pushing:

    python tools/check_no_pdk.py .

Exit code 0 = clean, 1 = findings.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Foundry names and well-known PDK/device identifiers (case-insensitive,
# matched on word boundaries). Extend as needed.
BLOCKED_TERMS = [
    r"tsmc", r"global\s*foundries", r"globalfoundries", r"gf\d{2,3}", r"umc\d*",
    r"smic", r"samsung\s+foundry", r"intel\s*\d+a", r"tower\s*semi\w*", r"towerjazz",
    r"x-?fab", r"skywater", r"sky130", r"gf180mcu", r"sg13g2", r"ihp\s*sg\w*",
    r"austriamicrosystems", r"ams\s+ag", r"powerchip", r"psmc", r"db\s*hitek",
    r"dongbu", r"magnachip", r"hua\s*hong", r"hhgrace", r"vanguard\s+international",
    r"nexchip", r"stmicro\w*", r"st\s*cmos\d+",
    # typical foundry device-name patterns
    r"nch_mac", r"pch_mac", r"nch_lvt\w*", r"pch_lvt\w*", r"nch_svt\w*", r"pch_svt\w*",
    r"nfet_01v8\w*", r"pfet_01v8\w*", r"nmos_rf\w*", r"pmos_rf\w*",
]

# File types that normally only come from a PDK
BLOCKED_SUFFIXES = {".tf", ".lyp", ".layermap", ".map", ".drf", ".lvs", ".drc",
                    ".rul", ".svrf", ".pvl", ".qrcTechFile", ".ict", ".itf"}
BLOCKED_NAMES = {"display.drf", "techfile.tf", "qrcTechFile", "layers.map"}

SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules"}
TEXT_SUFFIXES = {".md", ".txt", ".py", ".il", ".ils", ".ocn", ".scs", ".sp", ".va", ".vams",
                 ".v", ".sv", ".svh", ".vhd", ".tcl", ".sh", ".csh", ".f", ".json", ".yaml",
                 ".yml", ".csv", ".template", ".tmpl", ".cfg", ".env", ".log", ".psfascii", ""}

# Private-data patterns: (description, regex). Placeholders used in this repo
# (license-server, <server>, example.com, /path/to/...) are allowed below.
PRIVATE_PATTERNS = [
    ("license server (port@host)", re.compile(r"\b\d{4,5}@(?!license-server\b|<)[A-Za-z0-9][\w.-]*")),
    ("IPv4 address", re.compile(r"(?<![\w.])(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)(?![\w.])")),
    ("e-mail address", re.compile(r"\b[A-Za-z0-9._%+-]+@(?!example\.com\b|anthropic\.com\b)[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b")),
    ("home directory path (user name)", re.compile(r"(?:/home/|/Users/|/export/home/|[A-Z]:\\\\Users\\\\)(?!<|user\b|username\b|you\b)[A-Za-z0-9._-]+")),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("access token", re.compile(r"\b(?:ghp_[A-Za-z0-9]{20,}|github_pat_\w{20,}|glpat-[\w-]{20,}|AKIA[0-9A-Z]{16}|xox[bpas]-[\w-]{10,}|sk-[A-Za-z0-9_-]{20,})")),
]
ALLOWED_IPS = {"0.0.0.0", "127.0.0.1"}

# Lines containing this marker are ignored (for deliberate, reviewed mentions)
ALLOW_MARKER = "pdk-check: allow"

_PATTERN = re.compile(r"\b(" + "|".join(BLOCKED_TERMS) + r")\b", re.IGNORECASE)


def scan(root: Path):
    findings = []
    self_path = Path(__file__).resolve()
    for path in sorted(root.rglob("*")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file() or path.resolve() == self_path:
            continue
        rel = path.relative_to(root)
        if path.suffix in BLOCKED_SUFFIXES or path.name in BLOCKED_NAMES:
            findings.append((rel, 0, f"PDK-type file ({path.suffix or path.name})"))
            continue
        if path.suffix not in TEXT_SUFFIXES and not path.name.startswith("."):
            continue
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if ALLOW_MARKER in line:
                continue
            m = _PATTERN.search(line)
            if m:
                findings.append((rel, lineno, f"blocked term '{m.group(0)}'"))
            for desc, rx in PRIVATE_PATTERNS:
                for pm in rx.finditer(line):
                    if desc == "IPv4 address" and pm.group(0) in ALLOWED_IPS:
                        continue
                    findings.append((rel, lineno, f"possible private data: {desc} '{pm.group(0)}'"))
    return findings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    findings = scan(root)
    for rel, lineno, why in findings:
        loc = f"{rel}:{lineno}" if lineno else str(rel)
        print(f"{loc}: {why}")
    if findings:
        print(f"\n{len(findings)} finding(s). Remove PDK/foundry/private content, or mark a reviewed "
              f"line with '{ALLOW_MARKER}'.")
        return 1
    print(f"check_no_pdk: clean ({root})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
