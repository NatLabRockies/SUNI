# -*- coding: utf-8 -*-
"""SUNI base utilities"""
from math import sqrt


def format_date(year, month, day, year_first=False):
    """For mat date into string.

    Depending on the ``year_first``, the outputs will be
    `{year}-{month}-{day}` (``year_first = True``) or
    `{month}/{day}/{year}` (``year_first = False``).

    Parameters
    ----------
    year, month, day: int
        Integers representing the date.
    year_first : bool, optional
        Option to format with year first. By default, ``False``.

    Returns
    -------
    str
        Date formatted into string
    """
    if year_first:
        return f"{year}-{month}-{day}"
    return f"{month}/{day}/{year}"


def convert_to_year_first(date):
    """Convert input date to year-first format.

    Parameters
    ----------
    date : str
        Input date in month/day/year format.

    Returns
    -------
    str
        Date in year-month-day format.
    """
    month, day, year = date.split("/")
    return f"{year}-{month}-{day}"


def compute_parameter_stats(param_sum, param_sum_sq, sun_up_count, n_valid):
    """Compute mean and standard deviation from parameter accumulations.

    Parameters
    ----------
    param_sum : int | float
        The sum of the parameter across all records.
    param_sum_sq : int | float
        The squared sum of the parameter across all records.
    sun_up_count : int
        Number of records that correspond to a "sun up" measurement.
    n_valid : int
        Number of valid records.

    Returns
    -------
    mean, std : int |float
        Mean and standard deviation values fro parameter, or -9900 if
        the statistic cannot be computed from the inputs.
    """
    mean = (param_sum / sun_up_count) if sun_up_count > 0 else -9900
    if (divisor := (n_valid - 1)) > 0:
        std = sqrt((param_sum_sq - param_sum**2 / n_valid) / divisor)
    else:
        std = -9900
    return mean, std
