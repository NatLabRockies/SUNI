# fmt: off
"""Test the seriqc two-component test function."""
from pathlib import Path

import numpy as np
import pytest

from seriqc import SQC_2C
from seriqc.functions import seriqc_flag
from seriqc.gompertz_curves import boundary_from_gompertz_curve


@pytest.mark.parametrize("Kt", [0.01, 0.28, 1.04])
def test_two_component_zero_kn_inside_son_boundaries(Kt):
    left = boundary_from_gompertz_curve(7, 7, "left")
    right = boundary_from_gompertz_curve(5, 30, "right")
    result = SQC_2C(Kt, 0, 1.30, 0.76, left, right)
    assert result[:2] == (2, 2)


@pytest.mark.parametrize("Kt, Kn", [(0, 0), (1.06, 0), (0.28, -0.02)])
def test_two_component_outside_son_bottom_edge(Kt, Kn):
    left = boundary_from_gompertz_curve(7, 7, "left")
    right = boundary_from_gompertz_curve(5, 30, "right")
    result = SQC_2C(Kt, Kn, 1.30, 0.76, left, right)
    assert result[0] > 3
    assert result[1] > 3


def test_son_low_dni_three_component_regression():
    left = boundary_from_gompertz_curve(7, 7, "left")
    right = boundary_from_gompertz_curve(5, 30, "right")
    result = seriqc_flag(
        ghi=69, dni=3, dhi=69,
        zenith=79.55397177101352,
        dni_extra=1360.230055668625,
        ghi_extra=246.62202603615216,
        airmass=5.36,
        Kt_max=1.30, Kn_max=0.76, Kd_max=1.145,
        left_boundary=left, right_boundary=right,
    )
    assert result[:3] == (3, 3, 3)


def test_two_component_test_correct(bms_january_1min_boundaries):
    left_boundary, right_boundary, *K_max_vals = bms_january_1min_boundaries
    Kt_max, Kn_max, __ = K_max_vals
    ghi_flag_2, dni_flag_2 = SQC_2C(
        Kt=0.5,
        Kn=0.4,
        Kt_max=Kt_max,
        Kn_max=Kn_max,
        left_boundary=left_boundary,
        right_boundary=right_boundary,
        K_diff_threshold=0.01)
    # Check these flags are correct
    np.testing.assert_equal(ghi_flag_2, 2)
    np.testing.assert_equal(dni_flag_2, 2)


def test_two_component_test_correct_on_boundary(bms_january_1min_boundaries):
    # Test that flag is correctly set to 2, for a point on the boundary
    left_boundary, right_boundary, *K_max_vals = bms_january_1min_boundaries
    Kt_max, Kn_max, __ = K_max_vals
    ghi_flag_2, dni_flag_2 = SQC_2C(
        Kt=0.2,
        Kn=0.01,
        Kt_max=Kt_max,
        Kn_max=Kn_max,
        left_boundary=left_boundary,
        right_boundary=right_boundary,
        K_diff_threshold=0.01)
    # Check these flags are correct
    np.testing.assert_equal(ghi_flag_2, 2)
    np.testing.assert_equal(dni_flag_2, 2)


def test_two_component_test_correct_max_Kn(bms_january_1min_boundaries):
    # Test that flag is correctly set to 2, for a point on the boundary
    left_boundary, right_boundary, *K_max_vals = bms_january_1min_boundaries
    Kt_max, Kn_max, __ = K_max_vals
    ghi_flag_2, dni_flag_2 = SQC_2C(
        Kt=0.9,
        Kn=Kn_max,
        Kt_max=Kt_max,
        Kn_max=Kn_max,
        left_boundary=left_boundary,
        right_boundary=right_boundary,
        K_diff_threshold=0.01)
    # Check these flags are correct
    np.testing.assert_equal(ghi_flag_2, 2)
    np.testing.assert_equal(dni_flag_2, 2)


def test_two_component_test_correct_max_Kt(bms_january_1min_boundaries):
    # Test that flag is correctly set to 2, for a point on the boundary
    left_boundary, right_boundary, *K_max_vals = bms_january_1min_boundaries
    Kt_max, Kn_max, __ = K_max_vals
    ghi_flag_2, dni_flag_2 = SQC_2C(
        Kt=Kt_max,
        Kn=0.8,
        Kt_max=Kt_max,
        Kn_max=Kn_max,
        left_boundary=left_boundary,
        right_boundary=right_boundary,
        K_diff_threshold=0.01)
    # Check these flags are correct
    np.testing.assert_equal(ghi_flag_2, 2)
    np.testing.assert_equal(dni_flag_2, 2)


def test_two_component_test_correct_max_Kt_Kn(bms_january_1min_boundaries):
    # Test that flag is correctly set to 2, for a point on the boundary
    left_boundary, right_boundary, *K_max_vals = bms_january_1min_boundaries
    Kt_max, Kn_max, __ = K_max_vals
    ghi_flag_2, dni_flag_2 = SQC_2C(
        Kt=Kt_max,
        Kn=Kn_max,
        Kt_max=Kt_max,
        Kn_max=Kn_max,
        left_boundary=left_boundary,
        right_boundary=right_boundary,
        K_diff_threshold=0.01)
    # Check these flags are correct
    np.testing.assert_equal(ghi_flag_2, 2)
    np.testing.assert_equal(dni_flag_2, 2)


def test_two_component_greater_than_Kn_low_error(bms_january_1min_boundaries):
    # Kn>Kt but within Gompertz top boundary
    # Top_L=85.9 and Top_R=96
    left_boundary, right_boundary, *K_max_vals = bms_january_1min_boundaries
    Kt_max, Kn_max, __ = K_max_vals
    ghi_flag_2, dni_flag_2 = SQC_2C(
        Kt=0.9,
        Kn=Kn_max+0.04,  # Value has to be greater than K_diff_threshold
        Kt_max=Kt_max,
        Kn_max=Kn_max,
        left_boundary=left_boundary,
        right_boundary=right_boundary,
        K_diff_threshold=0.01)
    # Flags 16 and 17 correctly correspond to error between 0.04 and 0.05
    np.testing.assert_equal(ghi_flag_2, 24)
    np.testing.assert_equal(dni_flag_2, 25)


def test_two_component_greater_than_Kn_high_Kt_high(
        bms_january_1min_boundaries):
    # Add test case: Kn > Kn_max & Kt > Top_R
    left_boundary, right_boundary, *K_max_vals = bms_january_1min_boundaries
    Kt_max, Kn_max, __ = K_max_vals
    ghi_flag_2, dni_flag_2 = SQC_2C(
        Kt=0.97,
        Kn=Kn_max+0.05,
        Kt_max=Kt_max,
        Kn_max=Kn_max,
        left_boundary=left_boundary,
        right_boundary=right_boundary,
        K_diff_threshold=0.01)
    np.testing.assert_equal(ghi_flag_2, 29)
    np.testing.assert_equal(dni_flag_2, 28)


def test_two_component_Kn_below_zero_part_1(bms_january_1min_boundaries):
    # Add test case: (Kn < 0) & (Kt <= Bot_R) & (Kt >= Bot_L)
    left_boundary, right_boundary, *K_max_vals = bms_january_1min_boundaries
    Kt_max, Kn_max, __ = K_max_vals
    ghi_flag_2, dni_flag_2 = SQC_2C(
        Kt=0.4,
        Kn=-0.04 - 1e-6,  # Negative Kn
        Kt_max=Kt_max,
        Kn_max=Kn_max,
        left_boundary=left_boundary,
        right_boundary=right_boundary,
        K_diff_threshold=0.01)
    np.testing.assert_equal(ghi_flag_2, 25)
    np.testing.assert_equal(dni_flag_2, 24)


def test_two_component_Kn_below_zero_part_2(bms_january_1min_boundaries):
    # Add test case: # Add test case: (Kn < 0) & (Kt < Bot_L)
    left_boundary, right_boundary, *K_max_vals = bms_january_1min_boundaries
    Kt_max, Kn_max, __ = K_max_vals
    ghi_flag_2, dni_flag_2 = SQC_2C(
        Kt=-0.01 - 1e-6,
        Kn=-0.04 - 1e-6,  # Negative Kn
        Kt_max=Kt_max,
        Kn_max=Kn_max,
        left_boundary=left_boundary,
        right_boundary=right_boundary,
        K_diff_threshold=0.01)
    np.testing.assert_equal(ghi_flag_2, 24)
    np.testing.assert_equal(dni_flag_2, 25)


def test_two_component_greater_than_Kn_high_error(bms_january_1min_boundaries):
    # Similar to test_two_component_greater_than_Kn_low_error, but higher error
    left_boundary, right_boundary, *K_max_vals = bms_january_1min_boundaries
    Kt_max, Kn_max, __ = K_max_vals
    ghi_flag_2, dni_flag_2 = SQC_2C(
        Kt=0.9,
        Kn=Kn_max+0.08,  # Value has to be greater than K_diff_threshold
        Kt_max=Kt_max,
        Kn_max=Kn_max,
        left_boundary=left_boundary,
        right_boundary=right_boundary,
        K_diff_threshold=0.01)
    # Flags 16 and 17 correctly correspond to error between 0.04 and 0.05
    np.testing.assert_equal(ghi_flag_2, 40)
    np.testing.assert_equal(dni_flag_2, 41)


def test_two_component_greater_than_Kn_very_high_error(
        bms_january_1min_boundaries):
    # Similar to test_two_component_greater_than_Kn_very_high_error
    # This test has errors higher than 23%, hence the flags are 92-93
    # as errors that are greater than 23%, gets resolved to 23%.
    left_boundary, right_boundary, *K_max_vals = bms_january_1min_boundaries
    Kt_max, Kn_max, __ = K_max_vals
    ghi_flag_2, dni_flag_2 = SQC_2C(
        Kt=0.9,
        Kn=Kn_max+0.25,  # Value has to be than 0.23 (23%)
        Kt_max=Kt_max,
        Kn_max=Kn_max,
        left_boundary=left_boundary,
        right_boundary=right_boundary,
        K_diff_threshold=0.01)
    np.testing.assert_equal(ghi_flag_2, 92)
    np.testing.assert_equal(dni_flag_2, 93)


def test_two_component_greater_than_Kt_low_error(bms_january_1min_boundaries):
    # Tests flagging of a point to the immidiate right of Kt_max
    left_boundary, right_boundary, *K_max_vals = bms_january_1min_boundaries
    Kt_max, Kn_max, __ = K_max_vals
    ghi_flag_2, dni_flag_2 = SQC_2C(
        Kt=Kt_max+0.09,  # value has to be higher than K_diff_threshold
        Kn=0.2,
        Kt_max=Kt_max,
        Kn_max=Kn_max,
        left_boundary=left_boundary,
        right_boundary=right_boundary,
        K_diff_threshold=0.01)
    np.testing.assert_equal(ghi_flag_2, 93)
    np.testing.assert_equal(dni_flag_2, 92)


def test_two_component_point_right_of_gompertz(bms_january_1min_boundaries):
    # Test a point with low Kn and to the right of Gompertz curve and
    # Kt < Kt_max
    left_boundary, right_boundary, *K_max_vals = bms_january_1min_boundaries
    Kt_max, Kn_max, __ = K_max_vals
    ghi_flag_2, dni_flag_2 = SQC_2C(
        Kt=0.85,
        Kn=0.1,
        Kt_max=Kt_max,
        Kn_max=Kn_max,
        left_boundary=left_boundary,
        right_boundary=right_boundary,
        K_diff_threshold=0.01)
    np.testing.assert_equal(ghi_flag_2, 81)
    np.testing.assert_equal(dni_flag_2, 80)


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
