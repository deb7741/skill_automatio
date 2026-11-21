#!/usr/bin/env python3
"""Talk to a running Virtuoso from Python with skillbridge (read-only demo).

Setup (once):
    pip install skillbridge
    skillbridge path                 # prints the SKILL server file location
In the Virtuoso CIW:
    load("<printed path>")
    pyStartServer

Then:
    python3 skillbridge_demo.py                  # summary of libs + current cellview
    python3 skillbridge_demo.py --lib analogLib  # list cells of a library

skillbridge is open source: https://github.com/unihd-cag/skillbridge
"""

from __future__ import annotations

import argparse
import sys


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lib", help="list cells and views of this library")
    ap.add_argument("--workspace-id", default=None, help="skillbridge workspace id (if not default)")
    args = ap.parse_args(argv)

    try:
        from skillbridge import Workspace
    except ImportError:
        print("skillbridge not installed: pip install skillbridge", file=sys.stderr)
        return 2

    try:
        ws = Workspace.open(args.workspace_id) if args.workspace_id else Workspace.open()
    except Exception as exc:  # connection errors differ between versions
        print(f"Could not connect to Virtuoso ({exc}).\n"
              "Did you run load(\"<skillbridge path>\") and pyStartServer in the CIW?", file=sys.stderr)
        return 1

    # Any SKILL function can be called by name:
    print("Virtuoso version:", ws["getVersion"]())

    libs = ws["ddGetLibList"]()
    print(f"{len(libs)} libraries defined:", ", ".join(sorted(lib.name for lib in libs)))

    if args.lib:
        lib = ws["ddGetObj"](args.lib)
        if lib is None:
            print(f"library {args.lib!r} not found")
            return 1
        for cell in sorted(lib.cells, key=lambda c: c.name):
            print(f"  {cell.name:<30} {', '.join(v.name for v in cell.views)}")

    # The cellview in the current edit window (None if no window is open)
    cv = ws.ge.get_edit_cell_view()
    if cv is not None:
        print(f"\nEdit window: {cv.lib_name}/{cv.cell_name}/{cv.view_name}")
        print(f"  instances: {len(cv.instances or [])}  nets: {len(cv.nets or [])}")
        for inst in (cv.instances or [])[:20]:
            print(f"    {inst.name:<12} {inst.lib_name}/{inst.cell_name}")
    else:
        print("\n(no edit cellview open)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
