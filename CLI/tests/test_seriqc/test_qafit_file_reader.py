"""Test QA0 file reading utilities."""
from pathlib import Path

import pytest
import numpy as np

from seriqc.qafit_file_reader import (
    AirMassRegime,
    read_site_data_for_month,
    QA0FileError,
    extract_curve_numbers,
    extract_kn_kt,
)


def test_air_mass_regime_enum():
    """Test the Air Mass Regime enum"""
    assert AirMassRegime.LOW == 1
    assert AirMassRegime.MEDIUM == 2
    assert AirMassRegime.HIGH == 3

    assert str(AirMassRegime.LOW) == "low"
    assert str(AirMassRegime.MEDIUM) == "medium"
    assert str(AirMassRegime.HIGH) == "high"

    assert AirMassRegime.from_value(1) == AirMassRegime.LOW
    assert AirMassRegime.from_value(1.25) == AirMassRegime.LOW
    assert AirMassRegime.from_value(1.251) == AirMassRegime.MEDIUM
    assert AirMassRegime.from_value(2.49) == AirMassRegime.MEDIUM
    assert AirMassRegime.from_value(2.5) == AirMassRegime.MEDIUM
    assert AirMassRegime.from_value(2.51) == AirMassRegime.HIGH
    assert AirMassRegime.from_value(100) == AirMassRegime.HIGH


def test_read_site_data_for_month(qa0_info, tmp_path):
    """Test that `read_site_data_for_month` returns correct codes"""
    
    site, qa0_dir = qa0_info
    bad_qa0_fp = tmp_path / f"s_{site}.qa0"

    with pytest.raises(FileNotFoundError):
        read_site_data_for_month(site, tmp_path, 1)

    with open(Path(qa0_dir) / f"s_{site}.qa0", "r") as fh:
        lines = fh.readlines()

    lines[9] = lines[9].replace("JAN", "DNE")
    with open(bad_qa0_fp, "w") as fh:
        fh.writelines(lines)

    with pytest.raises(QA0FileError):
        read_site_data_for_month(site, tmp_path, 1)

    data, meta_1 = read_site_data_for_month(site, qa0_dir, 1)
    expected_data_from_line = [
        90,
        96,
        np.nan,
        np.nan,
        np.nan,
        np.nan,
        90,
        96,
        4,
        9,
        1,
        13,
        90,
        96,
        4,
        8,
        1,
        12,
    ]
    assert np.allclose(data.values, expected_data_from_line, equal_nan=True)

    data, meta_2 = read_site_data_for_month(site, qa0_dir, 3)
    expected_data_from_line = [
        85,
        94,
        4,
        10,
        1,
        12,
        85,
        94,
        4,
        9,
        2,
        15,
        85,
        94,
        4,
        9,
        1,
        13,
    ]
    assert np.allclose(data.values, expected_data_from_line, equal_nan=True)
    assert meta_1 == meta_2
    assert meta_1["latitude"] == 39.74
    assert meta_1["longitude"] == -105.18
    assert meta_1["tz"] == -7


def test_extract_curve_numbers(qa0_info):
    """Test the `extract_curve_numbers` function"""
    site, qa0_dir = qa0_info

    low, med, hi = AirMassRegime.LOW, AirMassRegime.MEDIUM, AirMassRegime.HIGH
    data, __ = read_site_data_for_month(site, qa0_dir, 1)
    assert extract_curve_numbers(data, 1, low) == (0, 0, 0, 0)
    assert extract_curve_numbers(data, 5, low) == (0, 0, 0, 0)
    assert extract_curve_numbers(data, 15, low) == (0, 0, 0, 0)
    assert extract_curve_numbers(data, 60, low) == (0, 0, 0, 0)

    assert extract_curve_numbers(data, 0.5, med) == (4, 1, 9, 16)
    assert extract_curve_numbers(data, 1, med) == (4, 1, 9, 16)
    assert extract_curve_numbers(data, 2, med) == (4, 1, 9, 16)
    assert extract_curve_numbers(data, 3, med) == (4, 1, 9, 13)
    assert extract_curve_numbers(data, 5, med) == (4, 1, 9, 13)
    assert extract_curve_numbers(data, 10, med) == (4, 1, 9, 0)
    assert extract_curve_numbers(data, 15, med) == (4, 1, 9, 0)
    assert extract_curve_numbers(data, 30, med) == (4, 1, 9, 0)
    assert extract_curve_numbers(data, 45, med) == (4, 1, 9, 13)
    assert extract_curve_numbers(data, 60, med) == (4, 1, 9, 13)

    assert extract_curve_numbers(data, 0.5, hi) == (4, 1, 8, 14)
    assert extract_curve_numbers(data, 1, hi) == (4, 1, 8, 14)
    assert extract_curve_numbers(data, 2, hi) == (4, 1, 8, 14)
    assert extract_curve_numbers(data, 3, hi) == (4, 1, 8, 12)
    assert extract_curve_numbers(data, 5, hi) == (4, 1, 8, 12)
    assert extract_curve_numbers(data, 10, hi) == (4, 1, 8, 0)
    assert extract_curve_numbers(data, 15, hi) == (4, 1, 8, 0)
    assert extract_curve_numbers(data, 30, hi) == (4, 1, 8, 0)
    assert extract_curve_numbers(data, 45, hi) == (4, 1, 8, 12)
    assert extract_curve_numbers(data, 60, hi) == (4, 1, 8, 12)


def test_extract_kn_kt(qa0_info):
    """Test the `extract_kn_kt` function"""
    site, qa0_dir = qa0_info

    data, __ = read_site_data_for_month(site, qa0_dir, 1)
    assert extract_kn_kt(data, 0.5) == (90, 96)
    assert extract_kn_kt(data, 1) == (90, 96)
    assert extract_kn_kt(data, 2) == (90, 96)
    assert extract_kn_kt(data, 3) == (90, 96)
    assert extract_kn_kt(data, 5) == (90, 96)
    assert extract_kn_kt(data, 10) == (90, 0)
    assert extract_kn_kt(data, 15) == (90, 0)
    assert extract_kn_kt(data, 30) == (90, 0)
    assert extract_kn_kt(data, 45) == (90, 96)
    assert extract_kn_kt(data, 60) == (90, 96)


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
