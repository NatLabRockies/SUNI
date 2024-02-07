# -*- coding: utf-8 -*-
"""SUNI instrument uncertainty computations"""
from math import sqrt


class _InstrumentUncertainties:
    ISO9060_PYRANOMETER_UNCERTAINTY = {"A": 2.4, "B": 5.2, "C": 11.9}
    ISO9060_PYRANOMETER_CAL_DEFAULT = {"A": 2, "B": 3, "C": 4}
    ISO9060_PYRHELIOMETER_UNCERTAINTY = {"A": 0.9, "B": 2.2, "C": 7.4}
    ISO9060_PYRHELIOMETER_CAL_DEFAULT = {"A": 0.8, "B": 1, "C": 3.5}

    def __init__(self, db=None):
        self.db = db
        self.pyranometer_uncertainty = None
        self.pyranometer_cal_default = None
        self.pyrheliometer_uncertainty = None
        self.pyrheliometer_cal_default = None
        self._load_values()

    def _load_values(self):
        if self.db is not None:
            raise NotImplementedError("Implementation is TODO!")

        self.pyranometer_uncertainty = self.ISO9060_PYRANOMETER_UNCERTAINTY
        self.pyranometer_cal_default = self.ISO9060_PYRANOMETER_CAL_DEFAULT
        self.pyrheliometer_uncertainty = self.ISO9060_PYRHELIOMETER_UNCERTAINTY
        self.pyrheliometer_cal_default = self.ISO9060_PYRHELIOMETER_CAL_DEFAULT

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
    for param, uncert, defaults in _InstrumentUncertainties():
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
