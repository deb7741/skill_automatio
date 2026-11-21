"""Tests for the command-line scripts (tool-independent paths only)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures"
PY = HERE.parent
sys.path.insert(0, str(PY))

import cadence_batch  # noqa: E402
import check_specs  # noqa: E402
import read_psf  # noqa: E402
import spectre_sweep  # noqa: E402
import xrun_regression  # noqa: E402


# ------------------------------------------------------------- read_psf --
def test_read_psf_bandwidth(capsys):
    assert read_psf.main([str(FIX / "rc_ac.psfascii"), "--bandwidth", "out", "--quiet"]) == 0
    assert float(capsys.readouterr().out) == pytest.approx(159155, rel=0.01)


def test_read_psf_csv(tmp_path):
    out = tmp_path / "ac.csv"
    read_psf.main([str(FIX / "rc_ac.psfascii"), "--csv", str(out), "--quiet"])
    header = out.read_text().splitlines()[0]
    assert header == "freq,in_re,in_im,out_re,out_im"


# -------------------------------------------------------- spectre_sweep --
def test_grid_and_render():
    grid = spectre_sweep.parse_param_args(["rval=1k,2k", "cval=1n"])
    points = spectre_sweep.expand_grid(grid)
    assert points == [{"rval": "1k", "cval": "1n"}, {"rval": "2k", "cval": "1n"}]
    assert spectre_sweep.point_name(points[0]) == "rval-1k_cval-1n"
    text = spectre_sweep.render_netlist("r=${rval} c=${cval}", points[1])
    assert text == "r=2k c=1n"


def test_render_missing_placeholder_fails():
    with pytest.raises(KeyError):
        spectre_sweep.render_netlist("r=${rval} x=${missing}", {"rval": "1k"})


def test_sweep_dry_run(tmp_path):
    tmpl = PY / "templates" / "rc_lowpass.scs.tmpl"
    rc = spectre_sweep.main([str(tmpl), "--param", "rval=1k,2k", "--param", "cval=1n",
                             "--out", str(tmp_path), "--dry-run"])
    assert rc == 0
    netlists = sorted(tmp_path.glob("*/input.scs"))
    assert len(netlists) == 2
    assert "parameters rval=2k cval=1n" in netlists[1].read_text()


def test_measure_from_fixture(tmp_path):
    raw = tmp_path / "psf"
    raw.mkdir()
    (raw / "ac1.ac").write_text((FIX / "rc_ac.psfascii").read_text())
    res = spectre_sweep.do_measure(raw, spectre_sweep.parse_measure_args(["bw:ac1.ac:out"]))
    assert res["bw"] == pytest.approx(159155, rel=0.01)


# ---------------------------------------------------------- check_specs --
def test_specs_wide_pass(tmp_path):
    specs = tmp_path / "s.json"
    specs.write_text(json.dumps({"bw": {"min": "30k"}}))
    assert check_specs.main([str(FIX / "sweep_summary.csv"), str(specs)]) == 0


def test_specs_wide_fail(tmp_path):
    specs = tmp_path / "s.json"
    specs.write_text(json.dumps({"bw": {"min": "100k"}}))
    rep = tmp_path / "r.md"
    assert check_specs.main([str(FIX / "sweep_summary.csv"), str(specs), "--report", str(rep)]) == 1
    assert "FAIL" in rep.read_text()


def test_specs_long_format(tmp_path):
    junit = tmp_path / "j.xml"
    rc = check_specs.main([str(FIX / "maestro_long.csv"), str(FIX / "specs.json"),
                           "--name-col", "Output", "--value-col", "Nominal",
                           "--label-cols", "Corner", "--junit", str(junit)])
    assert rc == 1                       # bw @ hot = 95k < 100k
    assert 'failures="1"' in junit.read_text()


def test_specs_missing_metric(tmp_path):
    specs = tmp_path / "s.json"
    specs.write_text(json.dumps({"gain_db": {"min": 40}}))
    assert check_specs.main([str(FIX / "sweep_summary.csv"), str(specs)]) == 1


# -------------------------------------------------------- cadence_batch --
def test_parse_ocean_results():
    text = "junk\nOCEAN_RESULT bw_hz=1.5e5 tr_s=2.2e-06\nOCEAN_RESULT corner=tt\n"
    assert cadence_batch.parse_ocean_results(text) == {"bw_hz": 1.5e5, "tr_s": 2.2e-6, "corner": "tt"}


def test_parse_batch_status():
    assert cadence_batch.parse_batch_status("x\nBATCH_STATUS: PASS\n") is True
    assert cadence_batch.parse_batch_status("BATCH_STATUS: PASS\nBATCH_STATUS: FAIL") is False
    assert cadence_batch.parse_batch_status("nothing") is None


# ------------------------------------------------------ xrun_regression --
def test_regression_dry_run(capsys):
    tests = PY.parent / "xrun" / "counter" / "tests.json"
    assert xrun_regression.main([str(tests), "--dry-run", "--tags", "smoke"]) == 0
    out = capsys.readouterr().out
    assert "[smoke]" in out and "-xmlibdirname" in out and "seed2" not in out


def test_regression_rejects_duplicates(tmp_path):
    f = tmp_path / "t.json"
    f.write_text(json.dumps({"tests": [{"name": "a"}, {"name": "a"}]}))
    with pytest.raises(ValueError, match="duplicate"):
        xrun_regression.load_tests(f)
