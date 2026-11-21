"""vautil: small, dependency-free helpers for Cadence simulation automation.

Modules
-------
psf_ascii : read Spectre PSF ASCII result files (``-format psfascii``)
measure   : waveform measurements (bandwidth, crossings, rise time, ...)
logparse  : parse Spectre and Xcelium/xrun logs into structured verdicts
junit     : write JUnit XML for CI dashboards
units     : parse/format engineering numbers ("1k", "2.5n", "1meg")
"""

__all__ = ["psf_ascii", "measure", "logparse", "junit", "units"]
__version__ = "0.1.0"
