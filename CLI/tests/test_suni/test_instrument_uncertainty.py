# -*- coding: utf-8 -*-
"""Instrument uncertainty tests. """
from pathlib import Path

import pytest

from suni.instrument_uncertainty import _InstrumentUncertainties

EXPECTED_DEFAULT_PYRANOMETER_UNCERTAINTY = {"A": 2.4, "B": 5.2, "C": 11.9}
EXPECTED_DEFAULT_PYRANOMETER_CAL_DEFAULT = {"A": 2, "B": 3, "C": 4}
EXPECTED_DEFAULT_PYRHELIOMETER_UNCERTAINTY = {"A": 0.9, "B": 2.2, "C": 7.4}
EXPECTED_DEFAULT_PYRHELIOMETER_CAL_DEFAULT = {"A": 0.8, "B": 1, "C": 3.5}
EXPECTED_DEFAULTS = {
    "GHI": (
        EXPECTED_DEFAULT_PYRANOMETER_UNCERTAINTY,
        EXPECTED_DEFAULT_PYRANOMETER_CAL_DEFAULT,
    ),
    "DNI": (
        EXPECTED_DEFAULT_PYRHELIOMETER_UNCERTAINTY,
        EXPECTED_DEFAULT_PYRHELIOMETER_CAL_DEFAULT,
    ),
    "DHI": (
        EXPECTED_DEFAULT_PYRANOMETER_UNCERTAINTY,
        EXPECTED_DEFAULT_PYRANOMETER_CAL_DEFAULT,
    ),
}


def test_instrument_uncertainties_class():
    """Test basic exec of instrument uncertainties class"""

    iu = _InstrumentUncertainties(db=None)
    for param, uncert, defaults in iu:
        assert param in {"GHI", "DNI", "DHI"}
        assert EXPECTED_DEFAULTS[param] == (uncert, defaults)


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
