"""Regressions for two-component flag differences from the C implementation."""

import re

import pytest

from seriqc.functions import SQC_2C, seriqc_flag
from seriqc.gompertz_curves import boundary_from_gompertz_curve


@pytest.mark.parametrize(
    "Kt, Kd, expected",
    [
        (0.42, 0.43, (13, 12)),
        (0.74, 0.76, (17, 16)),
        (0.61, 0.64, (21, 20)),
        (0.66, 0.70, (25, 24)),
        (1.00, 1.09, (45, 44)),
        (0.10, 0.15, (29, 28)),
        (0.60, 0.66, (33, 32)),
    ],
)
def test_negative_derived_kn_preserves_integer_percent(Kt, Kd, expected):
    left = boundary_from_gompertz_curve(7, 7, "left")
    right = boundary_from_gompertz_curve(5, 30, "right")
    result = SQC_2C(Kt, Kt - Kd, 1.30, 0.76, left, right)
    assert result[:2] == expected

    flags = seriqc_flag(
        ghi=Kt * 1000, dni=9900, dhi=Kd * 1000,
        zenith=45, dni_extra=1400, ghi_extra=1000, airmass=1.4,
        Kt_max=1.30, Kn_max=0.76, Kd_max=1.2,
        left_boundary=left, right_boundary=right,
    )
    assert flags[:3] == (expected[0], 99, expected[1])


@pytest.mark.parametrize(
    "left_shape, left_position, right_position, Kn_max, Kn, Kd, ghi",
    [
        (4, 10, 29, 0.84, 0.75, 0.52, 1310),
        (7, 7, 30, 0.80, 0.69, 0.58, 1290),
    ],
)
def test_derived_kt_at_clipped_right_boundary(
    left_shape, left_position, right_position, Kn_max, Kn, Kd, ghi,
):
    left = boundary_from_gompertz_curve(left_shape, left_position, "left")
    right = boundary_from_gompertz_curve(5, right_position, "right")
    result = SQC_2C(Kn + Kd, Kn, 1.27, Kn_max, left, right)
    assert result[:2] == (2, 2)

    flags = seriqc_flag(
        ghi=ghi, dni=Kn * 1400, dhi=Kd * 1000,
        zenith=45, dni_extra=1400, ghi_extra=1000, airmass=1.4,
        Kt_max=1.27, Kn_max=Kn_max, Kd_max=1.2,
        left_boundary=left, right_boundary=right,
    )
    assert flags[:3] == (8, 2, 2)


@pytest.mark.parametrize("Kt, Kn", [(1.28, 0.75), (1.27, 0.85)])
def test_points_beyond_clipped_boundary_still_fail(Kt, Kn):
    left = boundary_from_gompertz_curve(4, 10, "left")
    right = boundary_from_gompertz_curve(5, 29, "right")
    result = SQC_2C(Kt, Kn, 1.27, 0.84, left, right)
    assert result[0] > 3
    assert result[1] > 3


def test_pay_distance_includes_clipped_right_curve_points():
    left = boundary_from_gompertz_curve(7, 7, "left")
    right = boundary_from_gompertz_curve(7, 21, "right")
    result = SQC_2C(1.14, 0.53, 1.09, 0.68, left, right)
    assert result[:2] == (29, 28)

    flags = seriqc_flag(
        ghi=584, dni=738, dhi=312,
        zenith=68.2775717572143,
        dni_extra=1384.316758752284,
        ghi_extra=512.3499178954062,
        airmass=2.7, Kt_max=1.09, Kn_max=0.68, Kd_max=0.84,
        left_boundary=left, right_boundary=right,
    )
    assert flags[:3] == (8, 28, 28)
