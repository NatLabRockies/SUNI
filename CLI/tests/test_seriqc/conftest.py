"""SERIQC testing fixtures. """
import pytest

from seriqc.gompertz_curves import boundary_from_gompertz_curve


@pytest.fixture
def qc0_info(test_data_dir):
    """Site name and directory path, both as bytes."""
    return "BMS", str(test_data_dir)


@pytest.fixture
def bms_january_1min_boundaries():
    """BMS location 1 min interval Gompertz curve boundaries."""
    left_boundary = boundary_from_gompertz_curve(
        shape_number=4, position_number=1, side="left"
    )
    right_boundary = boundary_from_gompertz_curve(
        shape_number=1, position_number=14, side="right"
    )
    Kt_max = 0.96
    Kn_max = 0.9
    Kd_max = 0.19
    return left_boundary, right_boundary, Kt_max, Kn_max, Kd_max
