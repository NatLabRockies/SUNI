# -*- coding: utf-8 -*-
"""SUNI integrated tests"""
from pathlib import Path

import pytest

from suni.utilities import (
    format_date,
    convert_to_year_first,
    compute_parameter_stats,
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


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
