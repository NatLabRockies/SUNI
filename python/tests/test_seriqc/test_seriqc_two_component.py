# fmt: off
"""Test the seriqc two-component test function."""
from pathlib import Path

import numpy as np
import pytest

from seriqc import SQC_2C


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
        K_diff_threshold=0.03)
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
        K_diff_threshold=0.03)
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
        K_diff_threshold=0.03)
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
        K_diff_threshold=0.03)
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
        K_diff_threshold=0.03)
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
        K_diff_threshold=0.03)
    # Flags 16 and 17 correctly correspond to error between 0.04 and 0.05
    np.testing.assert_equal(ghi_flag_2, 16)
    np.testing.assert_equal(dni_flag_2, 17)


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
        K_diff_threshold=0.03)
    np.testing.assert_equal(ghi_flag_2, 21)
    np.testing.assert_equal(dni_flag_2, 20)


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
        K_diff_threshold=0.03)
    np.testing.assert_equal(ghi_flag_2, 17)
    np.testing.assert_equal(dni_flag_2, 16)


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
        K_diff_threshold=0.03)
    np.testing.assert_equal(ghi_flag_2, 16)
    np.testing.assert_equal(dni_flag_2, 17)


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
        K_diff_threshold=0.03)
    # Flags 16 and 17 correctly correspond to error between 0.04 and 0.05
    np.testing.assert_equal(ghi_flag_2, 32)
    np.testing.assert_equal(dni_flag_2, 33)


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
        K_diff_threshold=0.03)
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
        K_diff_threshold=0.03)
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
        K_diff_threshold=0.03)
    np.testing.assert_equal(ghi_flag_2, 73)
    np.testing.assert_equal(dni_flag_2, 72)


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
