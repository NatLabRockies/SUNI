"""Test SERIQC input utilities and validation function."""
from pathlib import Path

import numpy as np
import pytest

from seriqc.utilities import (
    validate_site,
    validate_time,
    convert_midnight,
    is_leap_year,
    conform_to_solpos_years,
    conform_to_spa_years,
    convert_to_day_of_year,
    convert_to_unix_time,
    validate_curve_numbers,
    validate_kn_kt,
    as_c_int,
    is_valid_three_component_record,
)


def test_validate_site():
    """Test that `validate_site` returns correct codes"""
    assert validate_site("TEST") == 0
    assert validate_site("      ") == 1
    assert validate_site("") == 1
    assert validate_site(None) == 1


def test_validate_time():
    """Test that `validate_time` returns correct codes"""
    assert validate_time(1, 1, 1, 1, 1) == 0

    # test month error
    assert validate_time(0, 1, 1, 1, 1) == 2
    assert validate_time(1, 1, 1, 1, 1) == 0
    assert validate_time(12, 1, 1, 1, 1) == 0
    assert validate_time(13, 1, 1, 1, 1) == 2

    # test day error
    assert validate_time(1, 0, 1, 1, 1) == 4
    assert validate_time(1, 1, 1, 1, 1) == 0
    assert validate_time(1, 31, 1, 1, 1) == 0
    assert validate_time(1, 32, 1, 1, 1) == 4

    # test hour error
    assert validate_time(1, 1, -1, 1, 1) == 8 | 32
    assert validate_time(1, 1, 0, 1, 1) == 0
    assert validate_time(1, 1, 24, 0, 1) == 0
    assert validate_time(1, 1, 25, 0, 1) == 8 | 32

    # test minute error
    assert validate_time(1, 1, 1, -1, 1) == 16
    assert validate_time(1, 1, 1, 0, 1) == 0
    assert validate_time(1, 1, 1, 59, 1) == 0
    assert validate_time(1, 1, 1, 60, 1) == 16

    # test time error
    assert validate_time(1, 1, 0, -1, 1) == 16 | 32
    assert validate_time(1, 1, 0, 0, 1) == 0
    assert validate_time(1, 1, 24, 0, 1) == 0
    assert validate_time(1, 1, 24, 1, 1) == 32

    # test interval error
    assert validate_time(1, 1, 1, 1, 0) == 64
    assert validate_time(1, 1, 1, 1, 1) == 0
    assert validate_time(1, 1, 1, 1, 60) == 0
    assert validate_time(1, 1, 1, 1, 61) == 64

    # test composition
    assert validate_time(0, 0, -1, -1, 0) == int("1111110", 2)
    assert validate_time(1, 0, -1, -1, 0) == int("1111100", 2)
    assert validate_time(1, 1, -1, -1, 0) == int("1111000", 2)
    assert validate_time(0, 1, -1, -1, 0) == int("1111010", 2)
    assert validate_time(0, 0, 1, 1, 1) == int("0000110", 2)


def test_convert_midnight():
    """Test the `convert_midnight` function."""
    assert convert_midnight(2001, 1, 1, 1, 0) == (2001, 1, 1, 1, 0)
    assert convert_midnight(2001, 1, 1, 0, 1) == (2001, 1, 1, 0, 1)

    assert convert_midnight(2001, 1, 2, 0, 0) == (2001, 1, 1, 24, 0)
    assert convert_midnight(2001, 3, 1, 0, 0) == (2001, 2, 28, 24, 0)
    assert convert_midnight(2001, 12, 1, 0, 0) == (2001, 11, 30, 24, 0)

    assert convert_midnight(2001, 1, 1, 0, 0) == (2000, 12, 31, 24, 0)
    assert convert_midnight(1, 1, 1, 0, 0) == (0, 12, 31, 24, 0)
    assert convert_midnight(0, 1, 1, 0, 0) == (99, 12, 31, 24, 0)

    assert convert_midnight(2000, 3, 1, 0, 0) == (2000, 2, 29, 24, 0)
    assert convert_midnight(2000, 4, 1, 0, 0) == (2000, 3, 31, 24, 0)
    assert convert_midnight(1900, 3, 1, 0, 0) == (1900, 2, 28, 24, 0)


def test_conform_to_solpos_years():
    """Test the `conform_to_solpos` function."""
    assert conform_to_solpos_years(49) == 2049
    assert conform_to_solpos_years(0) == 2000
    assert conform_to_solpos_years(50) == 1950
    assert conform_to_solpos_years(99) == 1999

    assert conform_to_solpos_years(100) == 1950
    assert conform_to_solpos_years(400) == 1952
    assert conform_to_solpos_years(2100) == 2050
    assert conform_to_solpos_years(2400) == 2048

    assert conform_to_solpos_years(1950) == 1950
    assert conform_to_solpos_years(2000) == 2000
    assert conform_to_solpos_years(2050) == 2050

    assert conform_to_solpos_years(1949) == 1950
    assert conform_to_solpos_years(2051) == 2050


def test_conform_to_spa_years():
    """Test the `conform_to_spa_years` function."""

    assert conform_to_spa_years(49) == 1970
    assert conform_to_spa_years(0) == 1972
    assert conform_to_spa_years(50) == 1970
    assert conform_to_spa_years(99) == 1970

    assert conform_to_spa_years(100) == 1970
    assert conform_to_spa_years(400) == 1972

    for year in range(1970, 2000):
        assert conform_to_spa_years(year) == year

    assert conform_to_spa_years(1969) == 1970
    assert conform_to_spa_years(1968) == 1972


def test_convert_to_day_of_year():
    """Test the `convert_to_day_of_year` function."""
    assert convert_to_day_of_year(1, 1, 2000) == 1
    assert convert_to_day_of_year(30, 1, 2000) == 30
    assert convert_to_day_of_year(1, 2, 2000) == 32
    assert convert_to_day_of_year(29, 2, 2000) == 31 + 29
    assert convert_to_day_of_year(1, 3, 2000) == 31 + 29 + 1
    assert convert_to_day_of_year(31, 12, 2000) == 366

    assert convert_to_day_of_year(28, 2, 2100) == 31 + 28
    assert convert_to_day_of_year(1, 3, 2100) == 31 + 28 + 1
    assert convert_to_day_of_year(31, 12, 2100) == 365


def test_is_leap_year():
    """Test the `is_leap_year` function."""
    assert is_leap_year(2000)
    assert not is_leap_year(2001)
    assert not is_leap_year(2100)


def test_convert_to_unix_time():
    """Test the `convert_to_unix_time` function."""
    assert convert_to_unix_time(2021, 7, 26, 21, 1)[0] == 1627333260
    assert convert_to_unix_time(2021, 7, 26, 21, 1, -7)[0] == (
        1627333260 + 7 * 60 * 60
    )


def test_validate_curve_numbers():
    """Test the `validate_curve_numbers` function."""
    assert validate_curve_numbers(1, 1, 1, 1) == 0
    assert validate_curve_numbers(0, 1, 1, 1) == 1 << 10
    assert validate_curve_numbers(1, 1, 0, 1) == 1 << 10
    assert validate_curve_numbers(0, 1, 0, 1) == 1 << 10

    assert validate_curve_numbers(1, 0, 1, 1) == 1 << 9
    assert validate_curve_numbers(1, 1, 1, 0) == 1 << 9
    assert validate_curve_numbers(1, 0, 1, 0) == 1 << 9

    assert validate_curve_numbers(1, 0, 0, 1) == 1 << 9 | 1 << 10
    assert validate_curve_numbers(0, 1, 1, 0) == 1 << 9 | 1 << 10
    assert validate_curve_numbers(0, 0, 0, 1) == 1 << 9 | 1 << 10
    assert validate_curve_numbers(1, 0, 0, 0) == 1 << 9 | 1 << 10


def test_validate_kn_kt():
    """Test the `validate_kn_kt` function."""
    assert validate_kn_kt(1, 1) == 0
    assert validate_kn_kt(0, 1) == 1 << 12
    assert validate_kn_kt(1, 0) == 1 << 11
    assert validate_kn_kt(0, 0) == 1 << 11 | 1 << 12


def test_as_c_int():
    """Test the `as_c_int` function."""
    assert as_c_int(0) == 0
    assert as_c_int(0.1) == 0
    assert as_c_int(0.9) == 0
    assert as_c_int(1.1) == 1

    assert as_c_int(-0) == 0
    assert as_c_int(-0.1) == 0
    assert as_c_int(-0.9) == 0
    assert as_c_int(-1.1) == -1

    assert np.isnan(as_c_int(float("NaN")))
    assert np.isnan(as_c_int(np.nan))


def test_is_valid_three_component_record():
    """Test the `is_valid_three_component_record` function."""

    assert not is_valid_three_component_record(0)
    assert not is_valid_three_component_record(1)
    assert not is_valid_three_component_record(2)
    assert is_valid_three_component_record(3)
    assert not is_valid_three_component_record(4)
    assert not is_valid_three_component_record(5)
    assert not is_valid_three_component_record(6)
    assert not is_valid_three_component_record(7)
    assert not is_valid_three_component_record(8)
    assert is_valid_three_component_record(9)
    assert is_valid_three_component_record(10)
    assert is_valid_three_component_record(11)
    assert not is_valid_three_component_record(12)
    assert not is_valid_three_component_record(13)
    assert is_valid_three_component_record(14)
    assert is_valid_three_component_record(15)
    assert is_valid_three_component_record(87)
    assert not is_valid_three_component_record(88)
    assert not is_valid_three_component_record(89)
    assert not is_valid_three_component_record(90)
    assert not is_valid_three_component_record(91)
    assert not is_valid_three_component_record(92)


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
