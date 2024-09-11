# -*- coding: utf-8 -*-
"""SUNI base utilities"""
from math import sqrt


def format_date(year, month, day, year_first=False):
    """Format date into string.

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


def extract_time_from_input_data(row, date_format):
    """Convert DATE+MST to integer date components.

    Parameters
    ----------
    row : pd.Series
        A series instance containing a "DATE" and "MST" column. "DATE"
        must have the format MM/DD/YYYY and "MST" must have the format
        HH:MM.
    date_format : int
        Integer representing the expected date format in the data.
        0: MM/DD/YYYY; 1: YYYY-MM-DD.


    Returns
    -------
    tuple
        Tuple of ints corresponding to the
        (year, month, day, hour, minute) represented by "DATE" and "MST"
        in the `row` input.
    """
    date = row["DATE"]
    try:
        if date_format:
            year, month, day = map(int, date.split("-"))
        else:
            month, day, year = map(int, date.split("/"))
    except ValueError:
        date_fmt_msg = {0: "0: MM/DD/YYYY", 1: "1: YYYY-MM-DD"}
        msg = (
            f"Input date ({date}) incompatible with data format "
            f"{date_fmt_msg[date_format]}"
        )
        raise ValueError(msg) from None

    hour, minute = map(int, row["MST"].split(":"))
    return year, month, day, hour, minute


def extract_irradiance_from_input_data(row):
    """Extract GHI, DNI, and DHI from row with NaN conversion.

    Specifically, values of < -9900 get converted to positive values.
    This is required by the SERIQC code.

    Parameters
    ----------
    row : pd.Series
        A series instance containing "GHI", "DNI", and "DHI" columns.
        Values in these columns that are set to be below -9900 are
        converted to positive values.

    Returns
    -------
    array-like
        "GHI", "DNI", and "DHI" values, where NaN representation is
        positive (required by SERIQC).
    """
    irradiance = row[["GHI", "DNI", "DHI"]].astype(float)
    irradiance[irradiance < -9900] *= -1
    return irradiance
