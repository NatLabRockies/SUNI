"""SERIQC input utilities and validation functions."""
from enum import IntEnum

import numpy as np
import pandas as pd


DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_MONTH_DAYS = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]


class ErrorCode(IntEnum):
    """Enumeration for SERIQC error codes.

    The intent is to define a number of error conditions and encode
    them in the SERI QC return code.  Each condition is represented
    by one bit in the integer return code (could be 16 bits or 32
    bits depending on the platform).  When an error condition is
    encountered, the appropriate bit is set.  Multiple bits may be
    set if more than one error condition is encountered.  After the
    call to SERI QC, the calling program should examine the return
    code; if it is zero (no bits set), the other return parameters
    are considered valid.  If the return code is non-zero, it can be
    decoded bit by bit to find out what condition caused the function
    to terminate. The :func:`seri_qc_decode` function does this and can
    also be a template for a more sophisticated decoder.

    Code         Bit  Parameter                Range or Error
    ===========  ===  =======================  ===================
    SITE         0    Site name                missing
    MONTH        1    Month                    1 - 12
    DAY          2    Day                      1 - 31
    HOUR         3    Hour                     0 - 24
    MINUTE       4    Minute                   0 - 59
    TIME         5    Composite Time           00:00:00 - 24:00:00
    INTERVAL     6    Interval                 1 - 60
    QC0_FILE     7    QC-ZERO file             missing
    QC0_FORMAT   8    QC-ZERO format           file format corrupt
    R_BOUND      9    QC-ZERO right boundary   boundary undefined
    L_BOUND      10   QC-ZERO left boundary    boundary undefined
    KT_MAX       11   QC-ZERO Kt max           boundary undefined
    KN_MAX       12   QC-ZERO Kn max           boundary undefined
    """

    SITE = 0
    MONTH = 1
    DAY = 2
    HOUR = 3
    MINUTE = 4
    TIME = 5
    INTERVAL = 6
    QC0_FILE = 7
    QC0_FORMAT = 8
    R_BOUND = 9
    L_BOUND = 10
    KT_MAX = 11
    KN_MAX = 12


def seri_qc_decode(code):  # pragma: no cover
    """Decode the return code from seriqc execution.

    The decoded errors are printed to the terminal.

    Parameters
    ----------
    code : int
        Return code from exec function.
    """
    if code & (1 << ErrorCode.SITE):
        print("SQC-decode ==> Site not found")
    if code & (1 << ErrorCode.MONTH):
        print("SQC-decode ==> Invalid month")
    if code & (1 << ErrorCode.DAY):
        print("SQC-decode ==> Invalid day")
    if code & (1 << ErrorCode.HOUR):
        print("SQC-decode ==> Invalid hour")
    if code & (1 << ErrorCode.MINUTE):
        print("SQC-decode ==> Invalid minute")
    if code & (1 << ErrorCode.TIME):
        print("SQC-decode ==> Invalid time")
    if code & (1 << ErrorCode.INTERVAL):
        print("SQC-decode ==> Invalid interval")
    if code & (1 << ErrorCode.QC0_FILE):
        print("SQC-decode ==> Cannot open QC-ZERO file")
    if code & (1 << ErrorCode.QC0_FORMAT):
        print("SQC-decode ==> Incorrect QC-ZERO file format")
    if code & (1 << ErrorCode.R_BOUND):
        print("SQC-decode ==> Right Gompertz boundary undefined")
    if code & (1 << ErrorCode.L_BOUND):
        print("SQC-decode ==> Left Gompertz boundary undefined")
    if code & (1 << ErrorCode.KT_MAX):
        print("SQC-decode ==> Kt max undefined")
    if code & (1 << ErrorCode.KN_MAX):
        print("SQC-decode ==> Kn max undefined")


def validate_site(site):
    """Validate site input.

    Parameters
    ----------
    site : str
        Name of site.

    Returns
    -------
    int
        0 if the site is valid (non-empty), otherwise 1
    """
    if site == "      " or not site:
        return 1 << ErrorCode.SITE
    return 0


def validate_time(month, day, hour, minute, interval):
    """Validate that time input is correct.

    This function return 0 if all time parameters are valid. Otherwise,
    a non-zero return code is provided, where teh value of the return
    code can be decoded using the :func:`seri_qc_decode` function. See
    the :cls:`ErrorCode` enum for full error code descriptions.

    Parameters
    ----------
    month : int | float
        Month value. Must be between 1 and 12 (inclusive) to pass test.
    day : int | float
        Day value. Must be between 1 and 31 (inclusive) to pass test.
    hour : int | float
        Hour value. Must be between 0 and 24 (inclusive) to pass test.
    minute : int | float
        Minute value. Must be between 0 and 59 (inclusive) to pass test.
    interval : int | float
        Interval value. Must be between 1 and 60 (inclusive) to pass
        test.

    Returns
    -------
    int
        Error code that can be decoded using the :func:`seri_qc_decode`
        function.
    """
    return_code = 0
    return_code |= _validate_parameter(month, 1, 12, ErrorCode.MONTH)
    return_code |= _validate_parameter(day, 1, 31, ErrorCode.DAY)
    return_code |= _validate_parameter(hour, 0, 24, ErrorCode.HOUR)
    return_code |= _validate_parameter(minute, 0, 59, ErrorCode.MINUTE)
    return_code |= _validate_parameter(
        hour * 60 + minute, 0, 1440, ErrorCode.TIME
    )
    return_code |= _validate_parameter(interval, 1, 60, ErrorCode.INTERVAL)
    return return_code


def _validate_parameter(param, lower, upper, error_code):
    """Validate that parameter is within inclusive bounds"""
    return 0 if lower <= param <= upper else 1 << error_code


def convert_midnight(year, month, day, hour, minute):
    """Convert time 00:00 to time 24:00 of the previous day.

    Parameters
    ----------
    year, month, day, hour, minute : int
        Time inputs broken into components: Year (any), month (1-12),
        day (1-31), hour (1-24), and minute (1-59). All intervals are
        inclusive.

    Returns
    -------
    year, month, day, hour, minute : int
        Year, month, day, hour, and minute inputs with 00:00 time
        converted to 24:00 of the previous day.
    """

    if hour or minute:
        return year, month, day, hour, minute

    hour = 24
    day -= 1
    if day:
        return year, month, day, hour, minute

    month -= 1
    if not month:
        month = 12
        year -= 1
        if year < 0:
            year = 99

    day = DAYS_IN_MONTH[month - 1]
    if is_leap_year(year) and month == 2:
        day += 1
    return year, month, day, hour, minute


def is_leap_year(year):
    """Check if an input year is a leap year.

    Leap year rules:
        1) The year must be divisible by 4.
        2) If the year is divisible by 100, it must also be divisible
           by 400.

    Parameters
    ----------
    year : int
        Year to check.

    Returns
    -------
    bool
        ``True`` if input year is leap year, otherwise ``False``.
    """
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def conform_to_solpos_years(year):
    """Conform to 1950-2050 valid range of S_solpos

    On 2000/01/21 SMW added this code to bound years to conform
    to the 1950-2050 valid range of S_solpos

    This includes converting two-digit years with a pivot:
        * 50-99 become 1950-1999; 00-49 become 2000-2049

    and mapping out of bound years to the closest valid year
        * 1950 or 2050, or leap year (1952 or 2048)

    Parameters
    ----------
    year : int
        Year to check.

    Returns
    -------
    int
        Year limited to the range 1950 - 2050. Leap years are converted
        to 1952 or 2048.
    """
    if year < 50:
        year += 2000
    elif year < 100:
        year += 1900

    ly = 2 if is_leap_year(year) else 0

    if year < 1950:
        year = 1950 + ly
    if year > 2050:
        year = 2050 - ly

    return year


def conform_to_spa_years(year):
    """Conform to SPA years.

    SPA required unix time input, which is only defined post 1970.
    Therefore, all years < 1970 are updated to the year 1970, with the
    exception of leap years, which are set to 1972. Years >= 1970 are
    unaffected.

    Parameters
    ----------
    year : int
        Year to check.

    Returns
    -------
    int
        Year limited to >= 1970. Years less than 1970 are set to 1970,
        except leap years < 1970, which are set to 1972.
    """
    ly = 2 if is_leap_year(year) else 0
    if year < 1970:
        year = 1970 + ly
    return year


def convert_to_day_of_year(day, month, year):
    """Convert a day to a day-of-year.

    Parameters
    ----------
    day : int
        Day of month ranging from 1 - 31.
    month : int
        Month of year ranging from 1 (Jan) to 12 (Dec).
    year : int
        Year under consideration (used for leap year calculations).

    Returns
    -------
    int
        Day of year ranging from 1 to 366.
    """
    day_of_year = day + _MONTH_DAYS[month - 1]
    if is_leap_year(year) and month > 2:
        day_of_year += 1
    return day_of_year


def convert_to_unix_time(year, month, day, hour, minute, timezone=None):
    """Convert input date to a unix time.

    Parameters
    ----------
    year, month, day, hour, minute : int
        Time inputs broken into components: Year (any), month (1-12),
        day (1-31), hour (1-24), and minute (1-59). All intervals are
        inclusive.
    timezone : int, optional
        Optional timezone offset value (UTC - X) to perform conversion
        to UTC. If ``None``, no conversion is performed.
        By default, ``None``.

    Returns
    -------
    np.array
        Numpy array with exactly one element, where the value is the
        unix time.
    """
    date = {
        "year": [year],
        "month": [month],
        "day": [day],
        "hour": [hour],
        "minute": [minute],
    }
    date = pd.to_datetime(date)
    if timezone:
        date += pd.Timedelta(hours=-timezone)
    return date.values.astype(np.int64) / 10**9


def validate_curve_numbers(
    left_shape, right_shape, left_position, right_position
):
    """Validate Gompertz curve codes for left and right bounds.

    Parameters
    ----------
    left_shape right_shape : int
        Code representing the left and right shape of the Gompertz
        curves. Undefined values should be represented as 0.
    left_position, right_position : int
        Code representing the left and right position of the Gompertz
        curves. Undefined values should be represented as 0.

    Returns
    -------
    int
        Return code (0 if all checks passed, non-zero otherwise).
    """
    return_value = 0
    if not all([left_shape, left_position]):
        return_value |= 1 << ErrorCode.L_BOUND
    if not all([right_shape, right_position]):
        return_value |= 1 << ErrorCode.R_BOUND
    return return_value


def validate_kn_kt(kn, kt):
    """Validate Kt and Kn values read from a QC0 file.

    Parameters
    ----------
    kn, kt : int
        Kn and Kt values read in from a QC0 file.

    Returns
    -------
    int
        Return code (0 if all checks passed, non-zero otherwise).
    """
    return_value = 0

    if not kn:
        return_value |= 1 << ErrorCode.KN_MAX
    if not kt:
        return_value |= 1 << ErrorCode.KT_MAX

    return return_value


def as_c_int(value):
    """Convert a value to an integer the same way C code would.

    This conversion is non-trivial for negative values. C code converts
    -0.1 to 0, -1.9 to -1, and so forth.

    Parameters
    ----------
    value : int | float
        Value to convert to integer like C code.

    Returns
    -------
    int
        Signed integer representation of the value, converted like C
        code would.
    """
    if np.isnan(value):
        return value

    val = int(np.floor(abs(value)))
    return np.sign(value) * val


def is_valid_three_component_record(ghi_flag):
    """Determine wether a data record has 3 valid components using GHI flag.

    Per the 6.4 deliverable::

        Data are valid for passing to the uncertainty calculations if
        the following conditions are met, which represent a valid
        three-component SERIQC flag:

            1.	Flag = 3 OR
            2.	Flag = 9 OR
            3.	Flag >=10 and <= 87 and ((Flag+2) mod 4) < 2.


    Parameters
    ----------
    ghi_flag : int
        SERIQC output GHI flag.

    Returns
    -------
    bool
        Wether the record contains valid three-component data.
    """
    is_3_or_9 = ghi_flag in {3, 9}
    in_valid_range = 10 <= ghi_flag <= 87
    has_valid_remainder = ((ghi_flag + 2) % 4) < 2
    return is_3_or_9 or (in_valid_range and has_valid_remainder)
