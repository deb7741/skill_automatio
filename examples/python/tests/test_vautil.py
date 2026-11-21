"""Unit tests for vautil and the CLI scripts. No Cadence tools required."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures"
sys.path.insert(0, str(HERE.parent))

from vautil import measure  # noqa: E402
from vautil.junit import TestResult, write_junit  # noqa: E402
from vautil.logparse import parse_spectre_log, parse_xrun_log  # noqa: E402
from vautil.psf_ascii import parse_psf_ascii, read_psf_ascii  # noqa: E402
from vautil.units import format_si, parse_si  # noqa: E402

F3DB = 1.0 / (2 * math.pi * 1e3 * 1e-9)  # 159.155 kHz


# ------------------------------------------------------------------ units --
@pytest.mark.parametrize("text,value", [
    ("1k", 1e3), ("2.5n", 2.5e-9), ("1meg", 1e6), ("1M", 1e6), ("3m", 3e-3),
    ("10uF", 10e-6), ("1e-9", 1e-9), ("-4.7p", -4.7e-12), ("100", 100.0), (5, 5.0),
])
def test_parse_si(text, value):
    assert parse_si(text) == pytest.approx(value)


def test_parse_si_rejects_garbage():
    with pytest.raises(ValueError):
        parse_si("abc")


def test_format_si():
    assert format_si(159154.9) == "159.2k"
    assert format_si(2.2e-6) == "2.2u"


# -------------------------------------------------------------- psf_ascii --
def test_read_ac_complex():
    d = read_psf_ascii(FIX / "rc_ac.psfascii")
    assert d.analysis_type == "ac"
    assert d.sweep_name == "freq"
    assert len(d.sweep_values) == 161
    assert set(d.traces) == {"in", "out"}
    assert isinstance(d.traces["out"][0], complex)
    assert d.units("out") == "V"


def test_read_tran_real():
    d = read_psf_ascii(FIX / "rc_tran.psfascii")
    assert d.sweep_name == "time"
    assert d.traces["out"][-1] == pytest.approx(1.0, abs=1e-6)


def test_read_dcop_scalars():
    d = read_psf_ascii(FIX / "dcop.psfascii")
    assert d.sweep_name is None
    assert d.scalars["out"] == pytest.approx(0.5)
    assert d.scalars["V1:p"] == pytest.approx(-5e-4)


def test_rejects_binary(tmp_path):
    f = tmp_path / "tran.tran"
    f.write_bytes(b"\x00\x00\x04\x00binary psf")
    with pytest.raises(ValueError, match="psfascii"):
        read_psf_ascii(f)


def test_missing_signal_message():
    d = read_psf_ascii(FIX / "rc_tran.psfascii")
    with pytest.raises(KeyError, match="available"):
        d.signal("nope")


def test_group_and_struct_tolerated():
    text = '''HEADER
"PSFversion" "1.00"
TYPE
"op" STRUCT(
"vgs" FLOAT DOUBLE
"ids" FLOAT DOUBLE
) PROP(
"key" "instance"
)
"V" FLOAT DOUBLE PROP(
"units" "V"
)
SWEEP
"time" "sweep"
TRACE
"grp" GROUP 2
"a" "V"
"b" "V"
VALUE
"time" 0
"a" 1
"b" 2
"time" 1e-9
"a" 3
"b" 4
END
'''
    d = parse_psf_ascii(text)
    assert d.traces["a"] == [1.0, 3.0]
    assert d.traces["b"] == [2.0, 4.0]


# ---------------------------------------------------------------- measure --
def test_bandwidth_matches_analytic():
    d = read_psf_ascii(FIX / "rc_ac.psfascii")
    bw = measure.bandwidth(d.sweep_values, d.traces["out"])
    assert bw == pytest.approx(F3DB, rel=0.01)


def test_rise_time_matches_analytic():
    d = read_psf_ascii(FIX / "rc_tran.psfascii")
    tr = measure.rise_time(d.sweep_values, d.traces["out"], v_initial=0.0, v_final=1.0)
    assert tr == pytest.approx(math.log(9) * 1e-6, rel=0.02)   # 2.197 * tau


def test_cross_and_value():
    t = [0.0, 1.0, 2.0, 3.0]
    y = [0.0, 1.0, 0.0, 1.0]
    assert measure.cross(t, y, 0.5, 1, "rising") == pytest.approx(0.5)
    assert measure.cross(t, y, 0.5, 2, "rising") == pytest.approx(2.5)
    assert measure.cross(t, y, 0.5, 1, "falling") == pytest.approx(1.5)
    assert measure.cross(t, y, 2.0) is None
    assert measure.value_at(t, y, 0.25) == pytest.approx(0.25)


def test_average_rms():
    t = [0.0, 1.0, 2.0]
    y = [1.0, 1.0, 1.0]
    assert measure.average(t, y) == pytest.approx(1.0)
    assert measure.rms(t, y) == pytest.approx(1.0)


# --------------------------------------------------------------- logparse --
def test_spectre_ok():
    log = parse_spectre_log(FIX / "spectre_ok.log")
    assert log.passed
    assert log.summary == {"errors": 0, "warnings": 1, "notices": 2}
    assert log.analysis_times_s["tran1"] == pytest.approx(15.2e-3)
    assert len(log.warnings) == 1


def test_spectre_fail():
    log = parse_spectre_log(FIX / "spectre_fail.log")
    assert not log.passed
    assert not log.completed
    assert log.errors[0].startswith("SFE-23")
    assert log.fatal_lines


def test_spectre_no_convergence():
    log = parse_spectre_log(FIX / "spectre_noconv.log")
    assert log.completed and not log.passed


def test_xrun_pass():
    log = parse_xrun_log(FIX / "xrun_pass.log")
    assert log.passed
    assert log.tool_warnings and not log.tool_errors


def test_xrun_fail_banner():
    assert not parse_xrun_log(FIX / "xrun_fail_banner.log").passed


def test_xrun_compile_error():
    log = parse_xrun_log(FIX / "xrun_compile_error.log")
    assert not log.passed
    assert any(e.startswith("CUVMUR") for e in log.tool_errors)


def test_xrun_uvm_errors():
    log = parse_xrun_log(FIX / "xrun_uvm.log")
    assert log.uvm["UVM_ERROR"] == 2
    assert not log.passed


def test_xrun_no_signal_is_not_pass():
    assert not parse_xrun_log("simulation ran\n", is_text=True).passed


# ------------------------------------------------------------------ junit --
def test_junit(tmp_path):
    out = write_junit([TestResult("a", True, 1.0), TestResult("b", False, 2.0, "boom")],
                      tmp_path / "j.xml")
    xml = out.read_text()
    assert 'tests="2"' in xml and 'failures="1"' in xml and "boom" in xml
