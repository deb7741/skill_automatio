#!/usr/bin/env python3
"""Inspect / export / measure a Spectre PSF ASCII result file.

Examples
--------
  read_psf.py psf/ac1.ac --list
  read_psf.py psf/ac1.ac --bandwidth out            # -3 dB bandwidth in Hz
  read_psf.py psf/tran1.tran --csv tran.csv          # all traces to CSV
  read_psf.py psf/tran1.tran --rise out              # 10-90 % rise time

Uses vautil.psf_ascii (no dependencies). Binary PSF / PSF-XL files must be
re-simulated with '-format psfascii' or converted with Cadence's 'psf' tool.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from vautil import measure  # noqa: E402
from vautil.psf_ascii import read_psf_ascii  # noqa: E402
from vautil.units import format_si  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("psf", help="PSF ASCII file, e.g. psf/tran1.tran")
    ap.add_argument("--list", action="store_true", help="list header info and signals")
    ap.add_argument("--csv", metavar="FILE", help="export sweep + all traces to CSV")
    ap.add_argument("--signals", nargs="+", help="restrict CSV export to these signals")
    ap.add_argument("--bandwidth", metavar="SIG", help="print -3 dB bandwidth of SIG (AC)")
    ap.add_argument("--rise", metavar="SIG", help="print 10-90%% rise time of SIG (tran)")
    ap.add_argument("--quiet", action="store_true", help="print bare numbers only")
    args = ap.parse_args(argv)

    data = read_psf_ascii(args.psf)

    if args.list or not (args.csv or args.bandwidth or args.rise):
        print(f"file      : {data.path}")
        print(f"analysis  : {data.analysis_type}")
        if data.sweep_name:
            print(f"sweep     : {data.sweep_name} ({len(data.sweep_values)} points, "
                  f"{data.sweep_values[0]:g} .. {data.sweep_values[-1]:g})")
        for name, vals in data.traces.items():
            kind = "complex" if vals and isinstance(vals[0], complex) else "real"
            print(f"  {name:<24} {data.units(name):<4} {kind}")
        for name, val in data.scalars.items():
            print(f"  {name:<24} = {val}")

    if args.csv:
        names = args.signals or list(data.traces)
        with open(args.csv, "w", newline="") as fh:
            w = csv.writer(fh)
            header = [data.sweep_name or "index"]
            for n in names:
                if data.traces[n] and isinstance(data.traces[n][0], complex):
                    header += [f"{n}_re", f"{n}_im"]
                else:
                    header.append(n)
            w.writerow(header)
            for k, x in enumerate(data.sweep_values):
                row = [repr(x)]
                for n in names:
                    v = data.traces[n][k]
                    row += [repr(v.real), repr(v.imag)] if isinstance(v, complex) else [repr(v)]
                w.writerow(row)
        if not args.quiet:
            print(f"wrote {args.csv}")

    rc = 0
    if args.bandwidth:
        bw = measure.bandwidth(data.sweep_values, data.signal(args.bandwidth))
        if bw is None:
            print("nan" if args.quiet else "bandwidth: no -3 dB crossing in sweep range")
            rc = 1
        else:
            print(f"{bw:.6g}" if args.quiet else f"bandwidth({args.bandwidth}) = {format_si(bw)}Hz")

    if args.rise:
        y = [float(abs(v)) if isinstance(v, complex) else float(v) for v in data.signal(args.rise)]
        tr = measure.rise_time(data.sweep_values, y, v_initial=min(y), v_final=max(y))
        if tr is None:
            print("nan" if args.quiet else "rise time: no rising edge found")
            rc = 1
        else:
            print(f"{tr:.6g}" if args.quiet else f"rise_time({args.rise}) = {format_si(tr)}s")
    return rc


if __name__ == "__main__":
    sys.exit(main())
