# -*- coding: utf-8 -*-
"""SUNI integrated tests"""
import json
import shutil
from pathlib import Path

import pytest
import pandas as pd

from suni.cli import main, process_from_config
from suni.framework import SERIQCError
from suni.utilities import convert_to_year_first
import suni.instrument_uncertainty

EXPECTED_GUI_REPORT = """
Uncertainty Processing Report for SRRL2004_01_testing.csv NRELSR

Beginning: 1/1/2004 0:00, Ending: 1/2/2004 8:00, Data records: 1921
Total eligible records: 421 (21.9%)
Exceeded SERIQC max: 0 (0.0%)

GHI Mean U95: +/-3.26% | Standard deviation: 0.37
DNI Mean U95: +/-1.48% | Standard deviation: 0.61
DHI Mean U95: +/-3.26% | Standard deviation: 0.37
"""
EXPECTED_EXTENDED_GUI_REPORT = """
Uncertainty Processing Report for SRRL2004_01_testing.csv NRELSR

Beginning: 2004-1-1 0:00, Ending: 2004-1-2 8:00, Data records: 1921
Total eligible records: 421 (21.9%)
Exceeded SERIQC max: 0 (0.0%)

GHI Mean U95: +/-3.26% | Standard deviation: 0.37
DNI Mean U95: +/-1.48% | Standard deviation: 0.61
DHI Mean U95: +/-3.26% | Standard deviation: 0.37

Urads Uncertainty Mean: +/-3.79%
Mean of System Uncertainty ABS: +/-2.36%
Field Uncertainty Mean: +/-0.47%
"""

def _validate_outputs(test_data_basic_run_dir, tmp_cwd, extended=False):
    for fn in ["SRRL2004_01_Unc.csv", "SRRL2004_01_Unc_report.txt"]:
        test_fp = tmp_cwd / fn
        assert test_fp.exists()

        if extended:
            fn = fn.replace(".csv", "_extended.csv")
            fn = fn.replace(".txt", "_extended.txt")

        truth_fp = test_data_basic_run_dir / fn

        with open(truth_fp, "r") as truth, open(test_fp, "r") as test:
            if "report" in fn:
                assert truth.readlines()[:3] == test.readlines()[:3]
                assert truth.readlines()[4:] == test.readlines()[4:]
            else:
                assert truth.readlines() == test.readlines()


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

    _validate_outputs(test_data_basic_run_dir, tmp_cwd)


def test_gui_report(tmp_cwd, test_data_basic_run_dir, capsys):
    """Test that the GUI report is as expected"""

    shutil.copy(test_data_basic_run_dir / "SRRL2004_01_testing.csv", tmp_cwd)
    shutil.copy(test_data_basic_run_dir / "s_NRELSR.qc0", tmp_cwd)

    assert len(list(tmp_cwd.glob("*"))) == 2

    with open(test_data_basic_run_dir / "sample_config.json") as fh:
        cfg = json.load(fh)

    out = process_from_config(cfg)

    captured = capsys.readouterr()
    assert captured.out.startswith("0\n")
    for percent in range(101):
        assert f"{percent}\n" in captured.out, f"{percent} pct not printed"

    assert isinstance(out, dict)
    assert out["report"] == EXPECTED_GUI_REPORT.strip("\n")

    assert len(list(tmp_cwd.glob("*"))) == 4

    _validate_outputs(test_data_basic_run_dir, tmp_cwd)


def test_gui_report_extended(tmp_cwd, test_data_basic_run_dir):
    """Test that the extended GUI report is as expected"""

    input_data = pd.read_csv(
        test_data_basic_run_dir / "SRRL2004_01_testing.csv",
        header=0,
        names=["DATE", "MST", "GHI", "DNI", "DHI"],
    )
    input_data["DATE"] = input_data["DATE"].map(convert_to_year_first)
    input_data.to_csv(tmp_cwd / "SRRL2004_01_testing.csv", index=False)
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

    _validate_outputs(test_data_basic_run_dir, tmp_cwd, extended=True)


def test_incompatible_data_format(tmp_cwd, test_data_basic_run_dir):
    """Test that the extended GUI report is as expected"""

    shutil.copy(test_data_basic_run_dir / "SRRL2004_01_testing.csv", tmp_cwd)
    shutil.copy(test_data_basic_run_dir / "s_NRELSR.qc0", tmp_cwd)

    assert len(list(tmp_cwd.glob("*"))) == 2

    with open(test_data_basic_run_dir / "sample_config.json") as fh:
        cfg = json.load(fh)

    cfg["ExtendedRpt"] = 1
    cfg["DateFormat"] = 1
    with pytest.raises(ValueError) as error:
        process_from_config(cfg, from_gui=False)

    assert "Input date" in str(error)
    assert "incompatible with data format (1: YYYY-MM-DD)" in str(error)


def test_report_no_cal_date(tmp_cwd, test_data_basic_run_dir):
    """Test that the report shows non-specified cal dates correctly"""

    input_data = pd.read_csv(
        test_data_basic_run_dir / "SRRL2004_01_testing.csv",
        header=0,
        names=["DATE", "MST", "GHI", "DNI", "DHI"],
    )
    input_data["DATE"] = input_data["DATE"].map(convert_to_year_first)
    input_data.to_csv(tmp_cwd / "SRRL2004_01_testing.csv", index=False)
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

    test_fp = tmp_cwd / "SRRL2004_01_Unc_report.txt"
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
        process_from_config(cfg, from_gui=False)

    assert "Non-zero SERIQC code: 2. Decoded to the following:" in str(error)
    assert "Invalid month" in str(error)


def test_seriqc_error_from_gui(tmp_cwd, test_data_dir):
    """Test that a non-zero SERIQC code writes error to file for GUI"""

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

    out = process_from_config(cfg, from_gui=True)

    expected_message = (
        "SERIQCError:\nError processing input data on line {}:\nNon-zero "
        "SERIQC code: 2. Decoded to the following:\n\t- Invalid month"
    )
    assert sum(out == expected_message.format(x) for x in range(2, 12)) == 1


def test_seriqc_error_bad_input_data(tmp_cwd, test_data_dir):
    """Test that a non-zero SERIQC code writes error to file for bad input"""

    shutil.copy(test_data_dir / "SRRL1987_05.csv", tmp_cwd / "SRRL1987_05.csv")
    shutil.copy(test_data_dir / "s_NRELSR.qc0", tmp_cwd)
    assert len(list(tmp_cwd.glob("*"))) == 2

    with open(test_data_dir / "basic_run" / "sample_config.json") as fh:
        cfg = json.load(fh)

    cfg["InputFile"] = "SRRL1987_05.csv"
    cfg["OutputFile"] = "SRRL1987_05_Unc.csv"
    cfg["max_workers"] = 2

    out = process_from_config(cfg, from_gui=True)

    expected_message = (
        "SUNIInputDataError:\nFound incorrect number of columns in input "
        "data! Ensure your input data has exactly the following columns: "
        '["DATE", "TIME", "GHI", "DNI", "DHI"]'
    )
    assert out == expected_message


def test_basic_run_new_instrument_uncertainty(
    tmp_cwd, test_data_basic_run_dir
):
    """Test basic run with user-input Instrument class and uncertainty."""
    shutil.copy(test_data_basic_run_dir / "SRRL2004_01_testing.csv", tmp_cwd)
    shutil.copy(test_data_basic_run_dir / "s_NRELSR.qc0", tmp_cwd)

    assert len(list(tmp_cwd.glob("*"))) == 2

    with open(test_data_basic_run_dir / "sample_config.json") as fh:
        cfg = json.load(fh)

    cfg["GHIcalUncert"] = 2
    cfg["GHIradUncert"] = 3.12

    cfg["DNIclassUncert"] = 5.2
    cfg["DNIcalUncert"] = 3
    cfg["DNIradUncert"] = 6

    cfg["DHIclass"] = "C"
    cfg["DHIclassUncert"] = 11.9
    cfg["DHIcalUncert"] = 4
    cfg["DHIradUncert"] = 12.55

    out = process_from_config(cfg, from_gui=True)
    assert "err_fp" not in out


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
