# -*- coding: utf-8 -*-
"""SUNI integrated tests"""
import json
import shutil
from pathlib import Path

import pytest
import pandas as pd

from suni.cli import main, process_from_config
from suni.framework import SERIQCError
import suni.instrument_uncertainty

EXPECTED_GUI_REPORT = """
Uncertainty Processing Report for SRRL2004_01_testing.csv NRELSR

Beginning: 1/1/2004 0:00, Ending: 1/2/2004 8:00, Data records: 1921
Total eligible records: 421 (21.9%)
Exceeded SERIQC max: 0 (0.0%)

GHI Mean U95: +/-2.30% | Standard deviation: 0.37
DNI Mean U95: +/-1.04% | Standard deviation: 0.61
DHI Mean U95: +/-2.30% | Standard deviation: 0.37
"""
EXPECTED_EXTENDED_GUI_REPORT = """
Uncertainty Processing Report for SRRL2004_01_testing.csv NRELSR

Beginning: 2004-1-1 0:00, Ending: 2004-1-2 8:00, Data records: 1921
Total eligible records: 421 (21.9%)
Exceeded SERIQC max: 0 (0.0%)

GHI Mean U95: +/-2.30% | Standard deviation: 0.37
DNI Mean U95: +/-1.04% | Standard deviation: 0.61
DHI Mean U95: +/-2.30% | Standard deviation: 0.37

Urads Uncertainty Mean: +/-2.67%
System Uncertainty Mean: +/-1.67%
Field Uncertainty Mean: +/-0.33%
"""


# @pytest.mark.skip
@pytest.mark.parametrize("config_ext", ("json", "ini"))
def test_basic_suni_run(
    tmp_cwd, test_data_basic_run_dir, cli_runner, config_ext, monkeypatch
):
    """Test basic end-to-end run"""

    og_add_instrument_uncertainties = (
        suni.instrument_uncertainty.add_instrument_uncertainties
    )

    def _rounded(config):
        config = og_add_instrument_uncertainties(config)
        config["GHIradUncert"] = round(config["GHIradUncert"], 1)
        config["DNIradUncert"] = round(config["DNIradUncert"], 1)
        config["DHIradUncert"] = round(config["DHIradUncert"], 1)
        return config

    monkeypatch.setattr(
        suni.instrument_uncertainty,
        "add_instrument_uncertainties",
        _rounded,
        raising=True,
    )

    shutil.copy(
        test_data_basic_run_dir / f"sample_config.{config_ext}", tmp_cwd
    )
    shutil.copy(test_data_basic_run_dir / "SRRL2004_01_testing.csv", tmp_cwd)
    shutil.copy(test_data_basic_run_dir / "s_NRELSR.qc0", tmp_cwd)

    assert len(list(tmp_cwd.glob("*"))) == 3

    result = cli_runner.invoke(
        main, [str(tmp_cwd / f"sample_config.{config_ext}")]
    )
    assert result.exit_code == 0, result.exception

    assert len(list(tmp_cwd.glob("*"))) == 5

    for fn in ["SRRL2004_01_Unc.csv", "SRRL2004_01_testing_Report.txt"]:
        truth_fp = test_data_basic_run_dir / fn
        test_fp = tmp_cwd / fn
        assert test_fp.exists()

        with open(truth_fp, "r") as truth, open(test_fp, "r") as test:
            assert truth.readlines()[2:] == test.readlines()[2:]


def test_gui_report(tmp_cwd, test_data_basic_run_dir):
    """Test that the GUI report is as expected"""

    shutil.copy(test_data_basic_run_dir / "SRRL2004_01_testing.csv", tmp_cwd)
    shutil.copy(test_data_basic_run_dir / "s_NRELSR.qc0", tmp_cwd)

    assert len(list(tmp_cwd.glob("*"))) == 2

    with open(test_data_basic_run_dir / "sample_config.json") as fh:
        cfg = json.load(fh)

    out = process_from_config(cfg)
    assert isinstance(out, dict)
    assert out["report"] == EXPECTED_GUI_REPORT.strip("\n")

    assert len(list(tmp_cwd.glob("*"))) == 4

    for fn in ["SRRL2004_01_Unc.csv", "SRRL2004_01_testing_Report.txt"]:
        truth_fp = test_data_basic_run_dir / fn
        test_fp = tmp_cwd / fn
        assert test_fp.exists()

        with open(truth_fp, "r") as truth, open(test_fp, "r") as test:
            assert truth.readlines()[2:] == test.readlines()[2:]


def test_gui_report_extended(tmp_cwd, test_data_basic_run_dir):
    """Test that the extended GUI report is as expected"""

    shutil.copy(test_data_basic_run_dir / "SRRL2004_01_testing.csv", tmp_cwd)
    shutil.copy(test_data_basic_run_dir / "s_NRELSR.qc0", tmp_cwd)

    assert len(list(tmp_cwd.glob("*"))) == 2

    with open(test_data_basic_run_dir / "sample_config.json") as fh:
        cfg = json.load(fh)

    cfg["ExtendedRpt"] = 1
    cfg["DateFormat"] = 1
    out = process_from_config(cfg)
    assert isinstance(out, dict)
    assert out["report"] == EXPECTED_EXTENDED_GUI_REPORT.strip("\n")

    assert len(list(tmp_cwd.glob("*"))) == 4

    for fn in ["SRRL2004_01_Unc.csv", "SRRL2004_01_testing_Report.txt"]:
        test_fp = tmp_cwd / fn
        assert test_fp.exists()

        fn = fn.replace(".csv", "_extended.csv")
        fn = fn.replace(".txt", "_extended.txt")
        truth_fp = test_data_basic_run_dir / fn

        with open(truth_fp, "r") as truth, open(test_fp, "r") as test:
            assert truth.readlines()[2:] == test.readlines()[2:]


def test_report_no_cal_date(tmp_cwd, test_data_basic_run_dir):
    """Test that the report shows non-specified cal dates correctly"""

    shutil.copy(test_data_basic_run_dir / "SRRL2004_01_testing.csv", tmp_cwd)
    shutil.copy(test_data_basic_run_dir / "s_NRELSR.qc0", tmp_cwd)

    assert len(list(tmp_cwd.glob("*"))) == 2

    with open(test_data_basic_run_dir / "sample_config.json") as fh:
        cfg = json.load(fh)

    cfg["ExtendedRpt"] = 1
    cfg["DateFormat"] = 1
    cfg["GHIcalDate"] = None
    cfg["GHIdueDate"] = ""
    out = process_from_config(cfg)
    assert isinstance(out, dict)
    assert out["report"] == EXPECTED_EXTENDED_GUI_REPORT.strip("\n")

    test_fp = tmp_cwd / "SRRL2004_01_testing_Report.txt"
    with open(test_fp, "r") as test:
        report_text = test.read()

    assert "Cal Date: Not specified" in report_text
    assert "Due Date: Not specified" in report_text


def test_raise_seriqc_error(tmp_cwd, test_data_dir):
    """Test that a non-zero SERIQC code raises an error"""

    df = pd.read_csv(
        test_data_dir / "SRRL2007_TIME_01.csv",
        header=0,
        names=[
            "DATE",
            "MST",
            "GHI",
            "DNI",
            "DHI",
            "C_GHI_FLG",
            "C_DNI_FLG",
            "C_DHI_FLG",
        ],
    )
    df[["DATE", "MST", "GHI", "DNI", "DHI"]].to_csv(
        tmp_cwd / "SRRL2007_TIME_01.csv", index=False
    )
    shutil.copy(test_data_dir / "s_NRELSR.qc0", tmp_cwd)

    assert len(list(tmp_cwd.glob("*"))) == 2

    with open(test_data_dir / "basic_run" / "sample_config.json") as fh:
        cfg = json.load(fh)

    cfg["InputFile"] = "SRRL2007_TIME_01.csv"
    cfg["OutputFile"] = "SRRL2007_TIME_01_Unc.csv"
    cfg["max_workers"] = 2

    with pytest.raises(SERIQCError) as error:
        process_from_config(cfg)

    assert "Non-zero SERIQC code: 2. Decoded to the following:" in str(error)
    assert "Invalid month" in str(error)


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
