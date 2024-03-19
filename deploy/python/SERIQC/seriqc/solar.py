"""SERIQC solar utilities"""
import numpy as np
from pvlib.spa import solar_position
from pvlib.irradiance import get_extra_radiation

from seriqc.utilities import (
    DAYS_IN_MONTH,
    is_leap_year,
    convert_to_unix_time,
    convert_to_day_of_year,
)

SOLAR_CONSTANT = 1361.1  # W/sq m
"""Solar constant (in W/m^2). Source: https://tinyurl.com/43xnwhh4"""


def compute_solar_properties(
    year,
    month,
    day,
    hour,
    minute,
    interval,
    lat,
    lon,
    timezone,
    elev=0,
    pressure=1013.25,
    temp=12,
    delta_t=67,
    atmos_refract=0.5667,
):
    """Compute solar properties for a given time/location.

    Compute the zenith angle, ETR, and ETRN by averaging the per-minute
    values.

    Parameters
    ----------
    year, month, day, hour, minute : int
        Time inputs broken into components: Year (any), month (1-12),
        day (1-31), hour (1-24), and minute (1-59). All intervals are
        inclusive.
    interval : int
        The measurement averaging interval (in minutes; 1-60).
    lat, lon : float
        Latitude and longitude of measurement location (in degrees).
    timezone : int
        Timezone offset value to perform conversion to UTC. Example
        input for Denver, Colorado is ``-7``.
    elev : int, optional
        Elevation of location, in meters. By default, ``0``.
    pressure : float, optional
        Pressure at location,  in millibars (used for atmospheric
        correction). By default, ``1013.25``.
    temp : int, optional
        Temperature at location, in Celsius (used for atmospheric
        correction). By default, ``12``.
    delta_t : int, optional
        Difference between terrestrial time and UT1. By default, ``67``.
    atmos_refract : float, optional
        The approximate atmospheric refraction (in degrees) at sunrise
        and sunset. By default, ``0.5667``.

    Returns
    -------
    solar_zenith_angle : float
        Solar zenith angle for input time (in degrees).
    etr, etrn: float
        Extraterrestrial and extraterrestrial normal irradiance
        (in W/m^2).

    See Also
    --------
    pvlib.spa.solar_position : Compute solar zenith angle.
    pvlib.solarposition.spa_python : Python implementation of SPA with
                                     default values for parameters
    """
    sol_zen = sun_up = etr = etrn = 0

    min_now = minute - interval
    hour_now = hour
    day_now = day
    month_now = month
    year_now = year

    if min_now < 0:
        out = _rewind_to_previous_hour(
            min_now, hour_now, day_now, month_now, year_now
        )
        min_now, hour_now, day_now, month_now, year_now = out

    for i in range(interval + 1):
        frac = 0.5 if i == 0 or i == interval else 1
        if min_now == 60:
            min_now = 0
            hour_now = hour
            day_now = day
            month_now = month
            year_now = year

        unix_time = convert_to_unix_time(
            year_now, month_now, day_now, hour_now, min_now, timezone
        )
        solar_zenith_now = solar_position(
            unixtime=unix_time,
            lat=lat,
            lon=lon,
            elev=elev,
            pressure=pressure,
            temp=temp,
            delta_t=delta_t,
            atmos_refract=atmos_refract,
            numthreads=8,
            sst=False,
            esd=False,
        )[0][0]

        etr_now, etrn_now = compute_etr_at_time(
            solar_zenith_now, day_now, month_now, year_now
        )

        if etr_now > 0:
            sun_up += frac
            sol_zen += solar_zenith_now * frac
            etr += etr_now * frac
            etrn += etrn_now * frac

        min_now += 1

    if sun_up > 0:
        sol_zen /= sun_up
        etr /= interval
        etrn /= interval
    else:
        sol_zen = 100

    return sol_zen, etr, etrn


def compute_etr_at_time(solar_zenith_angle, day, month, year):
    """Compute extraterrestrial irradiance for a given time.

    Parameters
    ----------
    solar_zenith_angle : float
        Solar zenith angle. Can be calculated using
        :func:`pvlib.spa.solar_position`.
    day, month, year : int
        Day (1-31), month (1-12), and year represented as integer
        values.

    Returns
    -------
    etr, etrn: float
        Extraterrestrial and extraterrestrial normal irradiance
        (in W/m^2).

    See Also
    --------
    pvlib.spa.solar_position : Compute solar zenith angle.
    pvlib.irradiance.get_extra_radiation : Compute extraterrestrial radiation.
    """
    doy = convert_to_day_of_year(day, month, year)
    etrn = get_extra_radiation(
        doy, solar_constant=SOLAR_CONSTANT, method="spencer", epoch_year=year
    )
    etr = etrn * np.cos(np.deg2rad(solar_zenith_angle))
    return etr, etrn


def _rewind_to_previous_hour(minute, hour, day, month, year):
    """Decrement hour with bounds checks. Not for public use."""
    minute += 60
    hour -= 1
    if hour < 0:
        hour, day, month, year = _rewind_to_previous_day(
            hour, day, month, year
        )
    return minute, hour, day, month, year


def _rewind_to_previous_day(hour, day, month, year):
    """Decrement day with bounds checks."""
    hour = 23
    day -= 1
    if day == 0:
        day, month, year = _rewind_to_previous_month(month, year)
    return hour, day, month, year


def _rewind_to_previous_month(month, year):
    """Decrement month with bounds checks."""
    month -= 1
    if month == 0:
        month, year = _rewind_to_previous_year(year)

    day = DAYS_IN_MONTH[month - 1]
    if is_leap_year(year) and month == 2:
        day += 1

    return day, month, year


def _rewind_to_previous_year(year):
    """Decrement year with bounds checks."""
    month = 12
    year -= 1
    if year < 0:
        year = 99
    return month, year
