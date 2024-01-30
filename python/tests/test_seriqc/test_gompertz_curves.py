"""Test Gompertz Boundary curve retrieval function."""
from pathlib import Path

import pytest
import numpy as np

from seriqc.gompertz_curves import boundary_from_gompertz_curve


def test_boundary_from_gompertz_curve():
    """Test the Gompertz curve values

    This test validates the following excerpt from the manual (pp. 95):

        For the set of curves that form the left boundaries, position
        1 (the leftmost position) of each shape passes through
        Kt = 0.35, Kn = 0.4

        ...

        For the set of curves that form the right boundaries, position
        1 (the leftmost curve) of all shapes passes through
        Kt = 0.475, Kn = 0.4.
    """
    for shape_number in range(1, 6):
        Kt, Kn = boundary_from_gompertz_curve(shape_number, 1, "left")
        ind = np.where(Kn == 0.4)[0][0]
        assert Kt[ind] == 0.35

        Kt, Kn = boundary_from_gompertz_curve(shape_number, 1, "right")
        ind = np.where(Kn == 0.4)[0][0]
        assert Kt[ind] == 0.475

    Kt, Kn = boundary_from_gompertz_curve(6, 1, "Left")
    ind = np.where(Kn == 0.4)[0][0]
    assert Kt[ind] == 0.35


@pytest.mark.parametrize(
    "shape_number, position_number, side",
    [
        (1, 1, "middle"),
        (0, 1, "left"),
        (7, 1, "left"),
        (0, 1, "right"),
        (7, 1, "left"),
    ],
)
def test_boundary_from_gompertz_curve_invalid_inputs(
    shape_number, position_number, side
):
    """Test invalid inputs to the `boundary_from_gompertz_curve` function"""
    with pytest.raises(ValueError):
        boundary_from_gompertz_curve(shape_number, position_number, side)


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
