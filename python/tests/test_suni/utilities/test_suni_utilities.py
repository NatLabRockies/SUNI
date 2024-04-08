# -*- coding: utf-8 -*-
"""SUNI integrated tests"""
from pathlib import Path

import pytest
import pandas as pd

from suni.utilities import (
    format_date,
    convert_to_year_first,
    compute_parameter_stats,
    extract_time_from_input_data,
    extract_irradiance_from_input_data,
)


def test_format_date():
    """Test the `format_date` function"""

    assert format_date(2000, 1, 15, year_first=True) == "2000-1-15"
    assert format_date(2000, 1, 15, year_first=False) == "1/15/2000"


def test_convert_to_year_first():
    """Test the `convert_to_year_first` function"""

    assert convert_to_year_first("1/15/2000") == "2000-1-15"


def test_compute_parameter_stats():
    """Test the `compute_parameter_stats` function"""

    assert compute_parameter_stats(0, 0, 0) == (-9900, -9900)
    assert compute_parameter_stats(100, 100, 1) == (100, -9900)
    assert compute_parameter_stats(0, 0, 100) == (0, 0)
    assert compute_parameter_stats(1000, 1000**2, 100) == (10, 100)


@pytest.mark.parametrize(
    "data_in, expected",
    (
        (("1/1/2021", "0:1", 0), (2021, 1, 1, 0, 1)),
        (("10/10/2020", "24:01", 0), (2020, 10, 10, 24, 1)),
        (("31/30/1998", "5:15", 0), (1998, 31, 30, 5, 15)),
        (("2021-1-1", "0:1", 1), (2021, 1, 1, 0, 1)),
        (("2020-10-10", "24:01", 1), (2020, 10, 10, 24, 1)),
        (("1998-31-30", "5:15", 1), (1998, 31, 30, 5, 15)),
    ),
)
def test_extract_time_from_input_data(data_in, expected):
    """Test the `extract_time_from_input_data` function"""

    time = {"DATE": data_in[0], "MST": data_in[1]}
    date_format = data_in[-1]
    assert extract_time_from_input_data(time, date_format) == expected


@pytest.mark.parametrize(
    "ghi, dni, dhi, expected",
    (
        (1, 1, 1, (1, 1, 1)),
        (-9999, 1, 9999, (9999, 1, 9999)),
    ),
)
def test_extract_irradiance_from_input_data(ghi, dni, dhi, expected):
    """Test the `extract_irradiance_from_input_data` function"""

    data_input = pd.Series({"GHI": ghi, "DNI": dni, "DHI": dhi})
    assert tuple(extract_irradiance_from_input_data(data_input)) == expected


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
