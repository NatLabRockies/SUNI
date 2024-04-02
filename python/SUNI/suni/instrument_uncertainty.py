# -*- coding: utf-8 -*-
"""SUNI instrument uncertainty computations"""
from math import sqrt
from pathlib import Path

import pandas as pd

from suni import REPO_DIR


class _InstrumentUncertainties:
    """Helper class to load instrument uncertainty values."""

    def __init__(self, db=None):
        """

        Parameters
        ----------
        db : path-like, optional
            Path to directory containing the "Upyranometer.csv" and
            "Upyrheliometer.csv" files. By default, ``None``.
        """
        self.db = Path(db or REPO_DIR / "instrument_database")
        self.pyranometer_uncertainty = None
        self.pyranometer_cal_default = None
        self.pyrheliometer_uncertainty = None
        self.pyrheliometer_cal_default = None
        self._load_values()

    def _load_values(self):
        """Load uncertainty values from teh database."""
        self.pyranometer_uncertainty, self.pyranometer_cal_default = (
            _read_instrument_data_from_file(self.db / "Upyranometer.csv")
        )
        self.pyrheliometer_uncertainty, self.pyrheliometer_cal_default = (
            _read_instrument_data_from_file(self.db / "Upyrheliometer.csv")
        )

    def __iter__(self):
        yield (
            "GHI",
            self.pyranometer_uncertainty,
            self.pyranometer_cal_default,
        )
        yield (
            "DNI",
            self.pyrheliometer_uncertainty,
            self.pyrheliometer_cal_default,
        )
        yield (
            "DHI",
            self.pyranometer_uncertainty,
            self.pyranometer_cal_default,
        )


def _read_instrument_data_from_file(fp):
    """read instrument data csv file."""
    if not fp.exists():
        raise FileNotFoundError(
            f"Did not find valid file in instrument database: {str(fp)}"
        )
    instrument_data = pd.read_csv(fp).set_index("Class")
    return (
        instrument_data["Uclass"].to_dict(),
        instrument_data["Ucal"].to_dict(),
    )


def add_instrument_uncertainties(config):
    """Add instrument uncertainties, if they are missing from the config.

    Parameters
    ----------
    config : : dict
        User input configuration dictionary, which may or may not
        contain the following keys:

            - GHIradUncert
            - DNIradUncert
            - DHIradUncert

        If any of these keys are missing, they will be fetched from a
        database (potentially on disk), and stored in the config.

    Returns
    -------
    dict
        Input config that definitely contains the "GHIradUncert",
        "DNIradUncert", and "DHIradUncert" keys.
    """
    iu = _InstrumentUncertainties(db=config.get("InstrumentDatabasePath"))
    for param, uncert, defaults in iu:
        rad_uncertainty_key = f"{param}radUncert"
        if rad_uncertainty_key in config:
            continue
        inst_class = config[f"{param}class"]
        inst_uncert = float(
            config.setdefault(f"{param}classUncert", uncert[inst_class])
        )
        cal_uncert = float(
            config.setdefault(f"{param}calUncert", defaults[inst_class])
        )
        config[rad_uncertainty_key] = sqrt(inst_uncert**2 + cal_uncert**2)

    return config


def extract_rad_uncertainty(config):
    """Extract radiometer uncertainty from config file.

    Note that if any instrument uncertainty params are not given in the
    config, they will be fetched from a database, potentially one on
    disk.

    Parameters
    ----------
    config : dict
        User input configuration dictionary, which may or may not
        contain the following keys:

            - GHIradUncert
            - DNIradUncert
            - DHIradUncert

        If any of these keys are missing, they will be fetched from a
        database (potentially on disk), and stored in the config.
        This method then returns the values for these three keys.

    Returns
    -------
    GHIradUncert, DNIradUncert, DHIradUncert
        Instrument irradiance uncertainties.
    """
    iup = ["GHIradUncert", "DNIradUncert", "DHIradUncert"]
    if any(param not in config for param in iup):
        config = add_instrument_uncertainties(config)
    ghi = float(config["GHIradUncert"])
    dni = float(config["DNIradUncert"])
    dhi = float(config["DHIradUncert"])
    return ghi, dni, dhi
