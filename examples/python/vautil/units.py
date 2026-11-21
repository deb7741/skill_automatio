"""Engineering-notation helpers compatible with Spectre/SKILL style numbers."""

from __future__ import annotations

import math
import re

# Spectre-mode suffixes (note: "M" = mega here, like Spectre/SKILL; use "meg"
# explicitly if your source is SPICE-mode where m/M both mean milli).
_SUFFIX = {
    "T": 1e12, "G": 1e9, "M": 1e6, "meg": 1e6, "MEG": 1e6, "K": 1e3, "k": 1e3,
    "_": 1.0, "%": 1e-2, "m": 1e-3, "u": 1e-6, "n": 1e-9, "p": 1e-12,
    "f": 1e-15, "a": 1e-18,
}
_NUM_RE = re.compile(
    r"^\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*(meg|MEG|[TGMKk_%munpfa])?\s*[a-zA-Z]*\s*$"
)


def parse_si(text: str | float | int) -> float:
    """Parse '1k', '2.5n', '1meg', '3e-9', '10uF' -> float.

    Trailing unit letters after the scale suffix are ignored ('10uF' -> 1e-05).
    Raises ValueError for anything else.
    """
    if isinstance(text, (int, float)):
        return float(text)
    m = _NUM_RE.match(str(text))
    if not m:
        raise ValueError(f"not a number: {text!r}")
    value = float(m.group(1))
    suffix = m.group(2)
    return value * _SUFFIX[suffix] if suffix else value


_FMT = [(1e12, "T"), (1e9, "G"), (1e6, "M"), (1e3, "k"), (1.0, ""),
        (1e-3, "m"), (1e-6, "u"), (1e-9, "n"), (1e-12, "p"), (1e-15, "f"),
        (1e-18, "a")]


def format_si(value: float, digits: int = 4) -> str:
    """Format a float with an engineering suffix: 159154.9 -> '159.2k'."""
    if value == 0 or not math.isfinite(value):
        return str(value)
    mag = abs(value)
    for scale, suffix in _FMT:
        if mag >= scale:
            return f"{value / scale:.{digits}g}{suffix}"
    return f"{value:.{digits}g}"
