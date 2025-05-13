# -*- coding: utf-8 -*-
"""SUNI integrated tests"""
import json
import shutil
from pathlib import Path
from itertools import product

import pytest
import pandas as pd

from suni.cli import main, process_from_config
from suni.framework import SERIQCError
from suni.utilities import convert_to_year_first
import suni.instrument_uncertainty
from suni.version import __version__

EXPECTED_GUI_REPORT = """
Uncertainty Processing Report for SRRL2004_01_testing.csv NRELSR

Beginning: 1/1/2004 0:00, Ending: 1/2/2004 8:00, Data records: 1921
Total eligible records: 421 (21.9%)
Exceeded SERIQC max: 0 (0.0%)

GHI Mean U95: +/-3.26% | Standard deviation: 0.37
DNI Mean U95: +/-1.48% | Standard deviation: 0.61
DHI Mean U95: +/-3.26% | Standard deviation: 0.37
"""
EXPECTED_EXTENDED_GUI_REPORT = f"""
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

SUNI v{__version__}
"""


def _no_9900_in_line(lines):
    """Replace any -9900 instances. """
    return [line.replace("-9900", "") for line in lines]


def _validate_outputs(test_data_basic_run_dir, tmp_cwd, extended=False):
    for fn in ["SRRL2004_01_Unc.csv", "SRRL2004_01_Unc_report.txt"]:
        test_fp = tmp_cwd / fn
        assert test_fp.exists()

        if extended:
            fn = fn.replace(".csv", "_extended.csv")
            fn = fn.replace(".txt", "_extended.txt")

        truth_fp = test_data_basic_run_dir / fn

        with open(truth_fp, "r") as truth, open(test_fp, "r") as test:
            truth_body = truth.readlines()
            test_body = _no_9900_in_line(test.readlines())
            if "report" in fn:
                assert truth_body[:3] == test_body[:3]
                if extended:
                    assert truth_body[4:] == test_body[4:-2]
                    assert test_body[-2:] == ["\n", f"SUNI v{__version__}"]
                else:
                    assert truth_body[4:] == test_body[4:]
            else:
                assert truth_body == test_body


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
    assert "incompatible with date format 1: YYYY-MM-DD" in str(error)


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


def test_date_parse_error_from_gui(tmp_cwd, test_data_dir):
    """Test that SUNI gives the expected message for bad date input"""

    ef_dir = test_data_dir / "extra_fields"
    shutil.copy(ef_dir / "s_NRELSR.qc0", tmp_cwd)
    df = pd.read_csv(
        ef_dir / "b1_extra_field_testing.csv",
        header=0,
        names=["DATE", "MST", "GHI", "DNI", "DHI"],
        index_col=False,
    )
    df.loc[0, "DATE"] = 1
    df[["DATE", "MST", "GHI", "DNI", "DHI"]].to_csv(
        tmp_cwd / "b1_extra_field_testing.csv", index=False
    )

    with open(test_data_dir / "extra_fields"/ "sample_config.json") as fh:
        cfg = json.load(fh)

    out = process_from_config(cfg, from_gui=True)
    expected_message = (
        "SUNIInputDataError:\nError processing input data on line 2:\n"
        "Input date (1) incompatible with date format 0: MM/DD/YYYY"
    )
    assert out == expected_message


def test_time_parse_error_from_gui(tmp_cwd, test_data_dir):
    """Test that SUNI gives the expected message for bad time input"""

    ef_dir = test_data_dir / "extra_fields"
    shutil.copy(ef_dir / "s_NRELSR.qc0", tmp_cwd)
    df = pd.read_csv(
        ef_dir / "b1_extra_field_testing.csv",
        header=0,
        names=["DATE", "MST", "GHI", "DNI", "DHI"],
        index_col=False,
    )
    df.loc[2, "MST"] = 1
    df[["DATE", "MST", "GHI", "DNI", "DHI"]].to_csv(
        tmp_cwd / "b1_extra_field_testing.csv", index=False
    )

    with open(test_data_dir / "extra_fields"/ "sample_config.json") as fh:
        cfg = json.load(fh)

    out = process_from_config(cfg, from_gui=True)
    expected_message = (
        "SUNIInputDataError:\nError processing input data on line 4:\n"
        "Input time (1) incompatible with expected time format HH:MM"
    )
    assert out == expected_message


@pytest.mark.parametrize("irr_data", [("GHI", 3), ("DNI", 4), ("DHI", 5)])
def test_irradiance_parse_error_from_gui(tmp_cwd, test_data_dir, irr_data):
    """Test that SUNI gives the expected message for bad time input"""

    ef_dir = test_data_dir / "extra_fields"
    shutil.copy(ef_dir / "s_NRELSR.qc0", tmp_cwd)
    df = pd.read_csv(
        ef_dir / "b1_extra_field_testing.csv",
        header=0,
        names=["DATE", "MST", "GHI", "DNI", "DHI"],
        index_col=False,
    )
    test_var, ind = irr_data
    df.loc[ind, test_var] = "a"
    df[["DATE", "MST", "GHI", "DNI", "DHI"]].to_csv(
        tmp_cwd / "b1_extra_field_testing.csv", index=False
    )

    with open(test_data_dir / "extra_fields"/ "sample_config.json") as fh:
        cfg = json.load(fh)

    out = process_from_config(cfg, from_gui=True)
    expected_message = (
        f"SUNIInputDataError:\nError processing input data on line {ind + 2}:"
        "\nOne or more of the following solar irradiance values cannot be "
        "parsed as a number"
    )
    assert expected_message in out
    assert f"'{test_var}': 'a'" in out


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


def test_extra_field(tmp_cwd, test_data_dir):
    """Test that extra fields in the input file don't crash the program"""

    ef_dir = test_data_dir / "extra_fields"
    shutil.copy(ef_dir / "b1_extra_field_testing.csv", tmp_cwd)
    shutil.copy(ef_dir / "s_NRELSR.qc0", tmp_cwd)

    with open(test_data_dir / "extra_fields"/ "sample_config.json") as fh:
        cfg = json.load(fh)

    out = process_from_config(cfg, from_gui=False)
    test_results = pd.read_csv(out["out_file"])
    assert len(test_results) == 6

def test_missing_fields(tmp_cwd, test_data_dir):
    """Test that missing fields in the input file raise correct error"""

    mf_dir = test_data_dir / "missing_fields"
    shutil.copy(mf_dir / "b1_missing_field_testing.csv", tmp_cwd)
    shutil.copy(mf_dir / "s_NRELSR.qc0", tmp_cwd)

    assert len(list(tmp_cwd.glob("*"))) == 2

    with open(mf_dir / "sample_config.json") as fh:
        cfg = json.load(fh)

    with pytest.raises(ValueError) as error:
        process_from_config(cfg, from_gui=False)

    assert "Found incorrect number of columns in input data!" in str(error)
    assert "Ensure your input data starts with at least" in str(error)
    assert '"DATE", "TIME", "GHI", "DNI", "DHI"' in str(error)

@pytest.mark.parametrize("flags", list(product([0, 1], [0, 1], [0, 1])))
def test_editable_class_uncertainty(tmp_cwd, test_data_dir, flags):
    """Test that the report highlights a user-edited uncertainty."""

    ef_dir = test_data_dir / "extra_fields"
    shutil.copy(ef_dir / "b1_extra_field_testing.csv", tmp_cwd)
    shutil.copy(ef_dir / "s_NRELSR.qc0", tmp_cwd)

    with open(test_data_dir / "extra_fields"/ "sample_config.json") as fh:
        cfg = json.load(fh)

    config_opts = ["GHIclassModFlg", "DNIclassModFlg", "DHIclassModFlg"]
    for opt, flag in zip(config_opts, flags):
        if flag:  # leave option out of config completely if it's false
            cfg[opt] = flag
    out = process_from_config(cfg)

    assert isinstance(out, dict)
    assert len(list(tmp_cwd.glob("*"))) == 4

    test_fp = tmp_cwd / "b1_extra_field_testing_Unc_report.txt"
    assert test_fp.exists()

    with open(test_fp, "r") as test:
        test_body = _no_9900_in_line(test.readlines())

    expected = "*| Cal Uncert"
    for ln, flag in zip([7, 8, 9], flags):
        if flag:
            assert expected in test_body[ln]
        else:
            assert expected not in test_body[ln]

    footnote = "   * indicates user override\n"
    if any(flags):
        assert test_body[10] == footnote
    else:
        assert test_body[10] != footnote


def test_missing_field_values(tmp_cwd, test_data_dir):
    """Test that missing fields in the input file raise correct error"""

    mf_dir = test_data_dir / "missing_field_value"
    shutil.copy(mf_dir / "b1_missing_field_value_testing.csv", tmp_cwd)
    shutil.copy(mf_dir / "s_NRELSR.qc0", tmp_cwd)

    assert len(list(tmp_cwd.glob("*"))) == 2

    with open(mf_dir / "sample_config.json") as fh:
        cfg = json.load(fh)

    out = process_from_config(cfg, from_gui=True)

    expected_message = (
        "SUNIInputDataError:\nError processing input data on line 7:"
        "\nOne or more solar irradiance values are missing. Please "
        "indicate missing data using the value '99999'"
    )
    assert out == expected_message


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
