"""Waveform measurements in plain Python (lists in, floats out).

These mirror common Ocean/ViVA calculator functions so post-processing can
run outside Virtuoso, in CI, without licenses.
"""

from __future__ import annotations

import math
from typing import List, Optional, Sequence, Union

Number = Union[float, complex]


def _interp(x0: float, y0: float, x1: float, y1: float, y: float) -> float:
    if y1 == y0:
        return x0
    return x0 + (y - y0) * (x1 - x0) / (y1 - y0)


def db20(values: Sequence[Number]) -> List[float]:
    """20*log10(|v|). Zero magnitude maps to -inf."""
    return [20.0 * math.log10(abs(v)) if abs(v) > 0 else float("-inf") for v in values]


def value_at(x: Sequence[float], y: Sequence[float], x_at: float) -> float:
    """Linear interpolation of y at x_at (like Ocean ``value(w x)``)."""
    if x_at <= x[0]:
        return float(y[0])
    for k in range(1, len(x)):
        if x[k] >= x_at:
            return float(y[k - 1] + (y[k] - y[k - 1]) * (x_at - x[k - 1]) / (x[k] - x[k - 1]))
    return float(y[-1])


def cross(x: Sequence[float], y: Sequence[float], threshold: float,
          n: int = 1, edge: str = "either") -> Optional[float]:
    """x position of the n-th crossing of ``threshold`` (like Ocean ``cross``).

    edge: 'rising', 'falling' or 'either'. Returns None if not found.
    """
    count = 0
    for k in range(1, len(x)):
        a, b = y[k - 1] - threshold, y[k] - threshold
        rising = a < 0 <= b
        falling = a > 0 >= b
        if (edge == "rising" and rising) or (edge == "falling" and falling) or \
           (edge == "either" and (rising or falling)):
            count += 1
            if count == n:
                return _interp(x[k - 1], y[k - 1], x[k], y[k], threshold)
    return None


def bandwidth(freq: Sequence[float], values: Sequence[Number], db_drop: float = 3.0,
              kind: str = "low") -> Optional[float]:
    """-N dB bandwidth (like Ocean ``bandwidth(w 3 "low")``).

    The reference is the magnitude at the first frequency point ('low') or the
    peak magnitude ('peak'). Interpolates linearly in log-frequency.
    """
    mags = db20(values)
    ref = mags[0] if kind == "low" else max(mags)
    target = ref - db_drop
    start = 0 if kind == "low" else mags.index(max(mags))
    for k in range(start + 1, len(freq)):
        if mags[k - 1] >= target > mags[k]:
            lf = _interp(math.log10(freq[k - 1]), mags[k - 1],
                         math.log10(freq[k]), mags[k], target)
            return 10.0 ** lf
    return None


def rise_time(t: Sequence[float], y: Sequence[float], lo_pct: float = 10.0,
              hi_pct: float = 90.0, v_initial: Optional[float] = None,
              v_final: Optional[float] = None) -> Optional[float]:
    """Time between lo_pct and hi_pct of the transition (first rising edge)."""
    v0 = y[0] if v_initial is None else v_initial
    v1 = y[-1] if v_final is None else v_final
    lo = v0 + (v1 - v0) * lo_pct / 100.0
    hi = v0 + (v1 - v0) * hi_pct / 100.0
    t_lo = cross(t, y, lo, 1, "rising")
    t_hi = cross(t, y, hi, 1, "rising")
    if t_lo is None or t_hi is None:
        return None
    return t_hi - t_lo


def ymax(y: Sequence[float]) -> float:
    return float(max(y))


def ymin(y: Sequence[float]) -> float:
    return float(min(y))


def average(t: Sequence[float], y: Sequence[float]) -> float:
    """Time-weighted average (trapezoidal), like Ocean ``average``."""
    area = sum((t[k] - t[k - 1]) * (y[k] + y[k - 1]) / 2.0 for k in range(1, len(t)))
    return area / (t[-1] - t[0])


def rms(t: Sequence[float], y: Sequence[float]) -> float:
    area = sum((t[k] - t[k - 1]) * (y[k] ** 2 + y[k - 1] ** 2) / 2.0 for k in range(1, len(t)))
    return math.sqrt(area / (t[-1] - t[0]))
