# fmt: off
"""Test the seriqc quality flagging functions."""
from pathlib import Path

import numpy as np
import pytest

from seriqc import seriqc_flag


def test_all_irradiance_missing():
    flags = seriqc_flag(ghi=np.nan, dni=np.nan, dhi=np.nan, zenith=45,
                        Kt_max=1, Kn_max=1, Kd_max=1,
                        dni_extra=1360, airmass=1)
    np.testing.assert_equal(flags, (99, 99, 99))


def test_extreme_high_irradiance_flagged_missing():
    # Irradiance that exceeds the nan_threshold irradiance level
    flags = seriqc_flag(ghi=8001, dni=8001, dhi=8001,
                        zenith=45, nan_threshold=8000,
                        Kt_max=1, Kn_max=1, Kd_max=1,
                        dni_extra=1360, airmass=1)
    np.testing.assert_equal(flags, (99, 99, 99))


def test_nan_threshold_works(bms_january_1min_boundaries):
    # This test is similar to the previous, except the nan_threshold is
    # increased above the irradiance values, which should not be flagged as nan
    left_boundary, right_boundary, *__ = bms_january_1min_boundaries
    flags = seriqc_flag(ghi=8001, dni=8001, dhi=8001,
                        zenith=45,
                        nan_threshold=8002,
                        left_boundary=left_boundary,
                        right_boundary=right_boundary,
                        Kt_max=1, Kn_max=1, Kd_max=1,
                        dni_extra=1360, airmass=1)
    assert flags[0] != 99
    assert flags[1] != 99
    assert flags[2] != 99


def test_minimum_daytime_values_one_component():
    # Test minimum daytime valus
    dni_extra = 1360
    # Minimum GHI test
    min_ghi = 0.05 * dni_extra * np.cos(np.deg2rad(45))
    flags = seriqc_flag(ghi=min_ghi-10, dni=np.nan, dhi=np.nan,
                        zenith=45, Kt_max=1, Kn_max=1, Kd_max=1,
                        dni_extra=dni_extra, airmass=2)
    assert flags[0] == 7
    # Test dni less than minimum irradiance thershold
    flags = seriqc_flag(ghi=np.nan, dni=-11, dhi=np.nan,
                        zenith=45, Kt_max=1, Kn_max=1, Kd_max=1,
                        dni_extra=dni_extra, airmass=2)
    assert flags[1] == 7
    min_dhi = 0.03 * dni_extra * np.cos(np.deg2rad(45))
    flags = seriqc_flag(ghi=np.nan, dni=np.nan, dhi=min_dhi-10,
                        zenith=45, Kt_max=1, Kn_max=1, Kd_max=1,
                        dni_extra=dni_extra, airmass=2)
    assert flags[2] == 7


def test_low_nighttime_irradiance():
    flags = seriqc_flag(ghi=-20, dni=-20, dhi=-20,
                        # nighttime
                        zenith=90,
                        # arbitrary values
                        Kt_max=1, Kn_max=1, Kd_max=1,
                        dni_extra=1360, airmass=1)
    np.testing.assert_equal(flags, (7, 7, 7))


def test_high_nighttime_irradiance():
    flags = seriqc_flag(ghi=100, dni=100, dhi=100,
                        # nighttime
                        zenith=95,
                        # arbitrary values
                        Kt_max=1, Kn_max=1, Kd_max=1,
                        dni_extra=1360, airmass=1)
    np.testing.assert_equal(flags, (8, 8, 8))


def test_good_data_point(bms_january_1min_boundaries):
    left_boundary, right_boundary, *K_max_vals = bms_january_1min_boundaries
    Kt_max, Kn_max, Kd_max = K_max_vals
    flags = seriqc_flag(
        ghi=400,
        dni=500,
        dhi=400 - 500 * np.cos(np.deg2rad(45)),
        zenith=45,
        dni_extra=1360,
        airmass=1.412,
        Kt_max=Kt_max,
        Kn_max=Kn_max,
        Kd_max=Kd_max,
        left_boundary=left_boundary,
        right_boundary=right_boundary,
        twilight_zenith=80,
        nan_threshold=8000,
        min_irradiance=-10,
        max_nighttime_irradiance=10,)
    np.testing.assert_equal(flags, (3, 3, 3))


def test_good_data_point_ghi_missing(bms_january_1min_boundaries):
    left_boundary, right_boundary, *K_max_vals = bms_january_1min_boundaries
    Kt_max, Kn_max, Kd_max = K_max_vals
    flags = seriqc_flag(
        ghi=np.nan,
        dni=100,
        dhi=400 - 100 * np.cos(np.deg2rad(45)),
        zenith=45,
        dni_extra=1360,
        airmass=1.412,
        Kt_max=Kt_max,
        Kn_max=Kn_max,
        Kd_max=Kd_max * 2,
        left_boundary=left_boundary,
        right_boundary=right_boundary,
        twilight_zenith=80,
        nan_threshold=8000,
        min_irradiance=-10,
        max_nighttime_irradiance=10,
        K_diff_threshold=0.03)
    np.testing.assert_equal(flags, (99, 2, 2))


@pytest.mark.parametrize('ghi,dni,flag', [
    (200, 400, 94),
    (160, 400, 95),
    (100, 400, 96),
    (80, 400, 97),
])
def test_Kn_higher_than_Kt_parametrized(
        ghi, dni, flag, bms_january_1min_boundaries):
    left_boundary, right_boundary, *K_max_vals = bms_january_1min_boundaries
    Kt_max, Kn_max, Kd_max = K_max_vals
    flags = seriqc_flag(
        ghi=ghi,
        dni=dni,
        dhi=np.nan,
        zenith=45,
        dni_extra=1360,
        airmass=1.412,
        Kt_max=Kt_max,
        Kn_max=Kn_max,
        Kd_max=Kd_max,
        left_boundary=left_boundary,
        right_boundary=right_boundary,
        )
    np.testing.assert_equal(flags, (flag, flag, 99))


def test_twilight_too_low_one_component_test(bms_january_1min_boundaries):
    left_boundary, right_boundary, *K_max_vals = bms_january_1min_boundaries
    Kt_max, Kn_max, Kd_max = K_max_vals
    flags = seriqc_flag(
        ghi=1,
        dni=np.nan,
        dhi=1,
        zenith=85,
        dni_extra=1360,
        airmass=10.3,
        Kt_max=Kt_max,
        Kn_max=Kn_max,
        Kd_max=Kd_max,
        left_boundary=left_boundary,
        right_boundary=right_boundary,
        )
    np.testing.assert_equal(flags, (1, 99, 1))


def test_twilight_too_high_one_component_test():
    # Test correct flagging of Kt > Kt_max during twilight period
    # Relevant condition: (ghi_flag == 8) & (ghi_extra <= 25) & (ghi <= 10)
    flags = seriqc_flag(
        ghi=9,
        dni=np.nan,
        dhi=np.nan,
        zenith=89.6,
        dni_extra=1360,
        airmass=26.3,
        Kt_max=0.9,
        Kn_max=np.nan,
        Kd_max=0.5)
    np.testing.assert_equal(flags, (1, 99, 99))


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
