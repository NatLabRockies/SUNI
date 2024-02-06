# -*- coding: utf-8 -*-
"""SUNI integrated tests"""
from pathlib import Path

import pytest

from suni.utilities import (
    format_date,
    convert_to_year_first,
    compute_parameter_stats,
    extract_time_from_input_data,
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

    assert compute_parameter_stats(0, 0, 0, 0) == (-9900, -9900)
    assert compute_parameter_stats(100, 100, 0, 1) == (-9900, -9900)
    assert compute_parameter_stats(0, 0, 100, 100) == (0, 0)
    assert compute_parameter_stats(1000, 1000**2, 100, 100) == (10, 100)


@pytest.mark.parametrize(
    "time_in, expected",
    (
        (("1/1/2021", "0:1"), (2021, 1, 1, 0, 1)),
        (("10/10/2020", "24:01"), (2020, 10, 10, 24, 1)),
        (("31/30/1998", "5:15"), (1998, 31, 30, 5, 15)),
    ),
)
def test_extract_time_from_input_data(time_in, expected):
    """Test the `extract_time_from_input_data` function"""

    time_in = {"DATE": time_in[0], "MST": time_in[1]}
    assert extract_time_from_input_data(time_in) == expected


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
