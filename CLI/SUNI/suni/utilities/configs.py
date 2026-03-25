"""SUNI config file loaders"""

import json
import configparser
from pathlib import Path


CONFIG_KEYS = [
    "StationID",
    "InputFile",
    "OutputFile",
    "SERIQCpath",
    "Interval",
    "GHIid",
    "GHImodel",
    "GHIclass",
    "GHIclassUncert",
    "GHIclassModFlg",
    "GHIcalUncert",
    "GHIcalDate",
    "GHIdueDate",
    "GHIradUncert",
    "DNIid",
    "DNImodel",
    "DNIclass",
    "DNIclassUncert",
    "DNIclassModFlg",
    "DNIcalUncert",
    "DNIcalDate",
    "DNIdueDate",
    "DNIradUncert",
    "DHIid",
    "DHImodel",
    "DHIclass",
    "DHIclassUncert",
    "DHIclassModFlg",
    "DHIcalUncert",
    "DHIcalDate",
    "DHIdueDate",
    "DHIradUncert",
    "MaxSysUncert",
    "MaxQC",
    "MinDNI",
    "MaxZEN",
    "DateFormat",
    "ExtendedRpt",
]


def data_from_ini(fp):
    """Load config data from INI file.

    Parameters
    ----------
    fp : path-like
        Path to INI config file.

    Returns
    -------
    dict
        Loaded config.
    """
    cfg = configparser.ConfigParser()
    cfg.read(fp)
    config = dict(cfg.items("SUNI"))

    return {
        key: config[key.lower()]
        for key in CONFIG_KEYS
        if key.lower() in config
    }


def data_from_json(fp):
    """Load config data from JSON file.

    Parameters
    ----------
    fp : path-like
        Path to JSON config file.

    Returns
    -------
    dict
        Loaded config.
    """
    with Path(fp).open("r", encoding="utf-8") as fh:
        return json.load(fh)
