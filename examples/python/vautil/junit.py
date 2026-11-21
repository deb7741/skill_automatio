"""Write JUnit XML (understood by Jenkins, GitLab, Azure DevOps, ...)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Union


@dataclass
class TestResult:
    __test__ = False  # not a pytest test class

    name: str
    passed: bool
    time_s: float = 0.0
    message: str = ""
    output: str = ""
    classname: str = "cadence"
    skipped: bool = False


def write_junit(results: Iterable[TestResult], path: Union[str, Path],
                suite_name: str = "cadence-regression") -> Path:
    results = list(results)
    failures = sum(1 for r in results if not r.passed and not r.skipped)
    skipped = sum(1 for r in results if r.skipped)
    suite = ET.Element("testsuite", name=suite_name, tests=str(len(results)),
                       failures=str(failures), errors="0", skipped=str(skipped),
                       time=f"{sum(r.time_s for r in results):.3f}")
    for r in results:
        case = ET.SubElement(suite, "testcase", classname=r.classname, name=r.name,
                             time=f"{r.time_s:.3f}")
        if r.skipped:
            ET.SubElement(case, "skipped", message=r.message or "skipped")
        elif not r.passed:
            fail = ET.SubElement(case, "failure", message=r.message or "failed")
            fail.text = r.output[-4000:] if r.output else None
        if r.output:
            out = ET.SubElement(case, "system-out")
            out.text = r.output[-4000:]
    tree = ET.ElementTree(ET.Element("testsuites"))
    tree.getroot().append(suite)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return path


def summary_line(results: Iterable[TestResult], label: Optional[str] = None) -> str:
    results = list(results)
    n_pass = sum(r.passed for r in results)
    head = f"{label}: " if label else ""
    return f"{head}{n_pass}/{len(results)} passed"
