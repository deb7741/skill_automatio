"""Turn Spectre and Xcelium logs into structured pass/fail verdicts.

Never trust exit codes alone: Spectre may exit 0 after convergence trouble,
and xrun exits 0 when a testbench reports UVM_ERRORs or prints FAILED.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

# ---------------------------------------------------------------- Spectre --

_SPECTRE_MSG = re.compile(r"^\s*(ERROR|WARNING|NOTICE)\s*\(([A-Za-z0-9_]+-\d+)\)\s*:?\s*(.*)$")
_SPECTRE_DONE = re.compile(
    r"completes with (\d+) errors?, (\d+) warnings?, and (\d+) notices?", re.I)
_SPECTRE_TIME = re.compile(
    r"Total time required for (\S+) analysis [`'\"]?([^'`\"]+)['`\"]?: CPU = ([\d.eE+-]+) ?(\w*s), elapsed = ([\d.eE+-]+) ?(\w*s)")
_SPECTRE_FATAL = re.compile(
    r"terminated prematurely|fatal error|No convergence achieved|time step too small|"
    r"Error found by spectre", re.I)

_TIME_SCALE = {"s": 1.0, "ms": 1e-3, "us": 1e-6, "ns": 1e-9, "min": 60.0, "h": 3600.0}


@dataclass
class SpectreLog:
    path: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    notices: int = 0
    summary: Optional[Dict[str, int]] = None          # from "completes with ..."
    analysis_times_s: Dict[str, float] = field(default_factory=dict)
    fatal_lines: List[str] = field(default_factory=list)

    @property
    def completed(self) -> bool:
        return self.summary is not None

    @property
    def passed(self) -> bool:
        n_err = self.summary["errors"] if self.summary else len(self.errors)
        return self.completed and n_err == 0 and not self.fatal_lines

    def to_dict(self) -> dict:
        d = asdict(self)
        d.update(completed=self.completed, passed=self.passed)
        return d


def parse_spectre_log(path_or_text: Union[str, Path], is_text: bool = False) -> SpectreLog:
    text = str(path_or_text) if is_text else Path(path_or_text).read_text(errors="replace")
    log = SpectreLog(path="<text>" if is_text else str(path_or_text))
    for line in text.splitlines():
        m = _SPECTRE_MSG.match(line)
        if m:
            level, code, msg = m.groups()
            entry = f"{code}: {msg.strip()}"
            if level == "ERROR":
                log.errors.append(entry)
            elif level == "WARNING":
                log.warnings.append(entry)
            else:
                log.notices += 1
        m = _SPECTRE_DONE.search(line)
        if m:
            log.summary = dict(zip(("errors", "warnings", "notices"), map(int, m.groups())))
        m = _SPECTRE_TIME.search(line)
        if m:
            _atype, aname, _cpu, _cu, elapsed, eu = m.groups()
            log.analysis_times_s[aname] = float(elapsed) * _TIME_SCALE.get(eu, 1.0)
        if _SPECTRE_FATAL.search(line):
            log.fatal_lines.append(line.strip())
    return log


# ---------------------------------------------------------------- Xcelium --

_XM_MSG = re.compile(r"\*([EFW]),([A-Z0-9_]+)\b(.*)$")
_UVM_SUM = re.compile(r"^\s*(UVM_ERROR|UVM_FATAL|UVM_WARNING)\s*:\s*(\d+)\s*$")
_PASS_RE = re.compile(r"\bTEST PASSED\b")
_FAIL_RE = re.compile(r"\bTEST FAILED\b")


@dataclass
class XrunLog:
    path: str
    tool_errors: List[str] = field(default_factory=list)    # *E / *F
    tool_warnings: List[str] = field(default_factory=list)  # *W
    uvm: Dict[str, int] = field(default_factory=dict)
    banner: Optional[str] = None                             # "PASSED" / "FAILED" / None

    @property
    def passed(self) -> bool:
        if self.tool_errors:
            return False
        if self.uvm.get("UVM_ERROR", 0) or self.uvm.get("UVM_FATAL", 0):
            return False
        if self.banner == "FAILED":
            return False
        # require a positive signal: PASS banner, or a UVM summary with zero errors
        return self.banner == "PASSED" or ("UVM_ERROR" in self.uvm)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["passed"] = self.passed
        return d


def parse_xrun_log(path_or_text: Union[str, Path], is_text: bool = False) -> XrunLog:
    text = str(path_or_text) if is_text else Path(path_or_text).read_text(errors="replace")
    log = XrunLog(path="<text>" if is_text else str(path_or_text))
    for line in text.splitlines():
        m = _XM_MSG.search(line)
        if m:
            sev, code, rest = m.groups()
            entry = f"{code}{rest}".strip()
            (log.tool_warnings if sev == "W" else log.tool_errors).append(entry)
        m = _UVM_SUM.match(line)
        if m:
            log.uvm[m.group(1)] = int(m.group(2))
        if _FAIL_RE.search(line):
            log.banner = "FAILED"
        elif _PASS_RE.search(line) and log.banner != "FAILED":
            log.banner = "PASSED"
    return log
