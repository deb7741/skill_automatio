"""Minimal, dependency-free reader for Spectre PSF ASCII files.

Generate them with ``spectre ... -format psfascii`` or convert existing
results with Cadence's ``psf`` utility (``psf -i tran1.tran -o out.psfascii``).

Supports the common cases used in automation:

* swept results (tran, ac, dc sweeps, noise, ...) with real or complex traces
* non-swept results (e.g. DC operating point "name" "type" value entries)

For full PSF support (binary, PSF-XL, structs) use ``libpsf`` or ``psf_utils``.

Example
-------
>>> from vautil.psf_ascii import read_psf_ascii
>>> d = read_psf_ascii("psf/ac1.ac")            # doctest: +SKIP
>>> d.sweep_name, len(d.sweep_values), list(d.traces)
('freq', 141, ['in', 'out'])
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Union

Number = Union[float, complex]

_TOKEN_RE = re.compile(
    r'"((?:[^"\\]|\\.)*)"'                     # 1: quoted string
    r"|(\()|(\))"                              # 2,3: parens
    r"|([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?|[+-]?(?:inf|nan))(?=[\s()]|$)"  # 4: number
    r"|([A-Za-z_][A-Za-z0-9_]*)"              # 5: bare word
)

_SECTIONS = {"HEADER", "TYPE", "SWEEP", "TRACE", "VALUE", "END"}


@dataclass
class PsfData:
    """Parsed content of one PSF ASCII file."""

    path: str
    header: Dict[str, object] = field(default_factory=dict)
    types: Dict[str, dict] = field(default_factory=dict)        # type name -> {"complex": bool, "props": {...}}
    sweep_name: Optional[str] = None
    sweep_values: List[float] = field(default_factory=list)
    trace_types: Dict[str, str] = field(default_factory=dict)   # trace -> type name
    traces: Dict[str, List[Number]] = field(default_factory=dict)
    scalars: Dict[str, object] = field(default_factory=dict)    # non-swept values

    @property
    def analysis_type(self) -> Optional[str]:
        return self.header.get("analysis type")  # type: ignore[return-value]

    def units(self, name: str) -> str:
        """Units of a trace (from its TYPE's "units" property), '' if unknown."""
        tname = self.trace_types.get(name, "")
        return str(self.types.get(tname, {}).get("props", {}).get("units", ""))

    def signal(self, name: str) -> List[Number]:
        try:
            return self.traces[name]
        except KeyError:
            raise KeyError(f"signal {name!r} not found; available: {sorted(self.traces)}") from None


class _Tokens:
    def __init__(self, text: str):
        self._toks = list(self._tokenize(text))
        self.i = 0

    @staticmethod
    def _tokenize(text: str) -> Iterator[tuple]:
        pos = 0
        n = len(text)
        while pos < n:
            if text[pos].isspace():
                pos += 1
                continue
            m = _TOKEN_RE.match(text, pos)
            if not m:
                raise ValueError(f"PSF parse error near: {text[pos:pos + 40]!r}")
            if m.group(1) is not None:
                yield ("str", m.group(1))
            elif m.group(2):
                yield ("(", "(")
            elif m.group(3):
                yield (")", ")")
            elif m.group(4) is not None:
                yield ("num", float(m.group(4)))
            else:
                yield ("word", m.group(5))
            pos = m.end()

    def peek(self, k: int = 0):
        j = self.i + k
        return self._toks[j] if j < len(self._toks) else (None, None)

    def next(self):
        tok = self.peek()
        self.i += 1
        return tok

    def at_section(self) -> bool:
        kind, val = self.peek()
        return kind == "word" and val in _SECTIONS

    def skip_balanced(self):
        """Skip a '( ... )' group (cursor must be on '(')."""
        kind, _ = self.next()
        assert kind == "("
        depth = 1
        while depth:
            kind, _ = self.next()
            if kind is None:
                raise ValueError("unbalanced parentheses in PSF file")
            depth += {"(": 1, ")": -1}.get(kind, 0)

    def read_props(self) -> dict:
        """Read 'PROP( "k" v "k" v ... )' (cursor on PROP)."""
        self.next()  # PROP
        props = {}
        kind, _ = self.next()
        assert kind == "("
        while True:
            kind, val = self.peek()
            if kind == ")":
                self.next()
                return props
            if kind == "str":
                self.next()
                k2, v2 = self.next()
                props[val] = v2
            else:  # unexpected token: skip
                if kind == "(":
                    self.skip_balanced()
                else:
                    self.next()


def _read_value(tk: _Tokens) -> object:
    kind, val = tk.peek()
    if kind == "num":
        tk.next()
        return val
    if kind == "str":
        tk.next()
        return val
    if kind == "(":
        # complex "(re im)" or a struct/array; return complex when 2 numbers
        tk.next()
        items = []
        while True:
            k2, v2 = tk.peek()
            if k2 == ")":
                tk.next()
                break
            if k2 == "(":
                tk.skip_balanced()
                items.append(None)
            else:
                tk.next()
                items.append(v2)
        if len(items) == 2 and all(isinstance(x, float) for x in items):
            return complex(items[0], items[1])
        return items
    tk.next()
    return val


def parse_psf_ascii(text: str, path: str = "<string>") -> PsfData:
    tk = _Tokens(text)
    data = PsfData(path=path)
    section = None
    swept = False

    while True:
        kind, val = tk.peek()
        if kind is None:
            break
        if tk.at_section():
            section = val
            tk.next()
            if section == "END":
                break
            continue

        if section == "HEADER":
            _, key = tk.next()
            data.header[str(key)] = _read_value(tk)

        elif section == "TYPE":
            _, tname = tk.next()
            info = {"complex": False, "props": {}}
            while not tk.at_section() and tk.peek()[0] not in ("str", None):
                k2, v2 = tk.peek()
                if k2 == "word" and v2 == "PROP":
                    info["props"] = tk.read_props()
                elif k2 == "word" and v2 == "COMPLEX":
                    info["complex"] = True
                    tk.next()
                elif k2 == "(":
                    tk.skip_balanced()       # STRUCT( ... ) / ARRAY( ... )
                else:
                    tk.next()
            data.types[str(tname)] = info

        elif section == "SWEEP":
            swept = True
            _, sname = tk.next()
            data.sweep_name = str(sname)
            if tk.peek()[0] == "str":
                tk.next()                     # sweep type name
            if tk.peek() == ("word", "PROP"):
                tk.read_props()

        elif section == "TRACE":
            _, name = tk.next()
            k2, v2 = tk.peek()
            if k2 == "word" and v2 == "GROUP":
                tk.next()
                tk.next()                     # member count; members follow as normal entries
                continue
            if k2 == "str":
                tk.next()
                data.trace_types[str(name)] = str(v2)
            data.traces.setdefault(str(name), [])
            if tk.peek() == ("word", "PROP"):
                tk.read_props()

        elif section == "VALUE":
            _, name = tk.next()
            name = str(name)
            if swept:
                value = _read_value(tk)
                if name == data.sweep_name:
                    data.sweep_values.append(float(value))  # type: ignore[arg-type]
                else:
                    data.traces.setdefault(name, []).append(value)  # type: ignore[arg-type]
            else:
                # non-swept: "name" "type" value  (type optional)
                if tk.peek()[0] == "str" and tk.peek(1)[0] in ("num", "("):
                    tk.next()
                data.scalars[name] = _read_value(tk)
            if tk.peek() == ("word", "PROP"):
                tk.read_props()
        else:
            tk.next()  # stray token before first section

    return data


def read_psf_ascii(path: Union[str, Path]) -> PsfData:
    """Read a PSF ASCII file from disk."""
    p = Path(path)
    head = p.read_bytes()[:64]
    if not head.lstrip().startswith(b"HEADER"):
        raise ValueError(
            f"{p} does not look like PSF ASCII (binary PSF/PSF-XL?). "
            "Re-run Spectre with '-format psfascii' or convert with 'psf -i <in> -o <out>'."
        )
    return parse_psf_ascii(p.read_text(errors="replace"), str(p))


def write_psf_ascii(path: Union[str, Path], sweep_name: str, sweep: List[float],
                    traces: Dict[str, List[Number]], analysis_type: str = "tran",
                    sweep_units: str = "s", trace_units: str = "V") -> None:
    """Write a simple swept PSF ASCII file (used for test fixtures and demos)."""
    is_complex = any(isinstance(v, complex) for vals in traces.values() for v in vals)
    lines = [
        "HEADER",
        '"PSFversion" "1.00"',
        '"simulator" "spectre"',
        f'"analysis type" "{analysis_type}"',
        f'"PSF sweep points" {len(sweep)}',
        f'"PSF traces" {len(traces)}',
        "TYPE",
        '"sweep" FLOAT DOUBLE PROP(', f'"units" "{sweep_units}"', '"key" "sweep"', ")",
        f'"V" {"COMPLEX" if is_complex else "FLOAT"} DOUBLE PROP(',
        f'"units" "{trace_units}"', '"key" "node"', ")",
        "SWEEP",
        f'"{sweep_name}" "sweep" PROP(', '"key" "sweep"', ")",
        "TRACE",
    ]
    lines += [f'"{name}" "V"' for name in traces]
    lines.append("VALUE")
    for k, x in enumerate(sweep):
        lines.append(f'"{sweep_name}" {x:.14e}')
        for name, vals in traces.items():
            v = vals[k]
            if is_complex:
                v = complex(v)
                lines.append(f'"{name}" ({v.real:.14e} {v.imag:.14e})')
            else:
                lines.append(f'"{name}" {float(v):.14e}')
    lines.append("END")
    Path(path).write_text("\n".join(lines) + "\n")
