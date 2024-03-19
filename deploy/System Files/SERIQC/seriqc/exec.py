"""Functions to execute SERI QC routine on a file."""
import logging
from pvlib.atmosphere import get_relative_airmass

from seriqc.utilities import (
    ErrorCode,
    validate_site,
    validate_time,
    convert_midnight,
    conform_to_spa_years,
    validate_curve_numbers,
    validate_kn_kt,
)
from seriqc.qcfit import (
    AirMassRegime,
    read_site_data_for_month,
    QC0FileError,
    extract_curve_numbers,
    extract_kn_kt,
)
from seriqc.gompertz_curves import boundary_from_gompertz_curve
from seriqc.solar import compute_solar_properties
from seriqc.functions import seriqc_flag


logger = logging.getLogger(__name__)
XD_MAX = [0.19, 0.22, 0.24, 0.28, 0.32]


def seriqc_from_file(
    site,
    qc0_dir,
    year,
    month,
    day,
    hour,
    minute,
    interval,
    ghi,
    dni,
    dhi,
    **kwargs,
):
    """Generate SERI-QC flags for one timestamp using QC0 file input.

    Performs QC checks on the major broadband solar measurements:
        Global Horizontal or Total (T)
        Direct Normal (N)
        Diffuse Horizontal (D)

    The time passed to this function should be the time of the END of
    the measurement.

    Only limits checking will be performed if the solar zenith angle
    exceeds 80 degrees.

    If any parameter is greater than ``nan_threshold``, it is assumed
    missing.

    Parameters
    ----------
    site : str
        Name of the site represented by the QC0 file. The QC0 file name
        must be of the format s_<site>.qc0, where <site> is replaced
        by this input.
    qc0_dir : path-like
        Path to directory containing the QC0 file(s) to read.
    year : int
        Year of the observation (e.g. 1988).
    month : int
        Month of the observation (1 = January, 12 = December).
    day : int
        Day of the month of the observation. Must be in the range 1-31
        (inclusive).
    hour : int
        Hour of the observation. Must be in the range 0-24 (inclusive).
    minute : int
        Minute of the observation. Must be in the range 0-59
        (inclusive).
    interval : int
        The measurement averaging interval (in minutes). Must be in the
        range 1-60 (inclusive).
    ghi : int | float
        Global horizontal broadband solar radiation (in W/m^2).
    dni : int | float
        Direct normal broadband solar radiation (in W/m^2).
    dhi : int | float
        Diffuse horizontal broadband solar radiation (in W/m^2).
    **kwargs
        Extra Keyword arguments to pass to
        :func:`seriqc.solar.compute_solar_properties` or
        :func:`seriqc.functions.seriqc_flag`.
        Allowed args for :func:`seriqc.solar.compute_solar_properties`:

            - ``elev``
            - ``pressure``
            - ``temp``
            - ``delta_t``
            - ``atmos_refract``

        Allowed args for :func:`seriqc.functions.seriqc_flag`:

            - ``twilight_zenith``
            - ``nan_threshold``
            - ``min_irradiance``
            - ``max_nighttime_irradiance``
            - ``K_diff_threshold``


    Returns
    -------
    ghi_flag : int
        Global horizontal irradiance quality control flag.
    dni_flag : int
        Direct normal irradiance quality control flag.
    dhi_flag : int
        Diffuse horizontal irradiance quality control flag.
    etr : float
        Extraterrestrial radiation (in W/m^2; 0 if code errors out).
    etrn : float
        Extraterrestrial normal radiation (in W/m^2; 0 if code errors
        out).
    sol_zen : float
        Solar zenith angle for input time (in degrees; 0 if code errors
        out).
    return_code : int
        Integer value representing the return code. Can be decoded
        using the :func:`seriqc.utilities.seri_qc_decode` function.
    """
    global_out = direct_out = diffuse_out = return_value = 0
    etr = etrn = sol_zen = 0
    return_value |= validate_site(site)
    return_value |= validate_time(month, day, hour, minute, interval)
    if return_value:
        return (
            global_out,
            direct_out,
            diffuse_out,
            etr,
            etrn,
            sol_zen,
            return_value,
        )
    year, month, day, hour, minute = convert_midnight(
        year, month, day, hour, minute
    )

    # PP: The original C code used the SOLPOS algorithm so the call below
    # used to be "year = conform_to_solpos_years(year)", where the
    # `conform_to_solpos_years` function was imported from seriqc.utilities
    # Since the python version uses the SPA algorithm instead of SOLPOS,
    # the call below was updated to use `conform_to_spa_years`
    year = conform_to_spa_years(year)

    try:
        data, meta = read_site_data_for_month(site, qc0_dir, month)
    except FileNotFoundError:
        return_value |= 1 << ErrorCode.QC0_FILE
        return (
            global_out,
            direct_out,
            diffuse_out,
            etr,
            etrn,
            sol_zen,
            return_value,
        )
    except QC0FileError:
        return_value |= 1 << ErrorCode.QC0_FORMAT
        return (
            global_out,
            direct_out,
            diffuse_out,
            etr,
            etrn,
            sol_zen,
            return_value,
        )

    spa_kwargs = {}
    spa_kwargs["elev"] = kwargs.pop("elev", 0)
    spa_kwargs["pressure"] = kwargs.pop("pressure", 1013.25)
    spa_kwargs["temp"] = kwargs.pop("temp", 12)
    spa_kwargs["delta_t"] = kwargs.pop("delta_t", 67)
    spa_kwargs["atmos_refract"] = kwargs.pop("atmos_refract", 0.5667)
    sol_zen, etr, etrn = compute_solar_properties(
        year,
        month,
        day,
        hour,
        minute,
        interval,
        meta["latitude"],
        meta["longitude"],
        meta["tz"],
        **spa_kwargs,
    )

    if etr == 0:
        global_out, direct_out, diffuse_out = seriqc_flag(
            ghi=ghi,
            dni=dni,
            dhi=dhi,
            zenith=90,
            dni_extra=None,
            airmass=None,
            Kt_max=None,
            Kn_max=None,
            Kd_max=None,
            **kwargs,
        )
        return (
            global_out,
            direct_out,
            diffuse_out,
            etr,
            etrn,
            sol_zen,
            return_value,
        )

    air_mass = get_relative_airmass(sol_zen, model="kastenyoung1989")
    logger.debug(
        f"Airmass: {air_mass:.4f} Solzen: {sol_zen:.4f} ETR: {etr:.4f}"
    )
    nam = AirMassRegime.from_value(air_mass)

    out = extract_curve_numbers(data, interval, nam)
    left_shape, right_shape, left_position, right_position = out
    kn, kt = extract_kn_kt(data, interval)

    return_value |= validate_curve_numbers(
        left_shape, right_shape, left_position, right_position
    )
    return_value |= validate_kn_kt(kn, kt)
    if return_value:
        logger.debug(
            f"    - P - Solzen: {sol_zen:.6f}, ETR: {etr:.6f}, "
            f"ETRN {etrn:.6f}, XT: {global_out / etr:.6f}, "
            f"KT: {(global_out / etr)*100 + 0.5:.6f}, "
            f"XN: {direct_out / etrn:.6f}, "
            f"KN: {(direct_out / etrn)*100 + 0.5:.6f}, "
            f"XD: {diffuse_out / etr:.6f}, "
            f"KD: {(diffuse_out / etr)*100 + 0.5:.6f}"
        )
        global_out = direct_out = diffuse_out = 0
        return (
            global_out,
            direct_out,
            diffuse_out,
            etr,
            etrn,
            sol_zen,
            return_value,
        )

    xd_max = XD_MAX[right_shape - 1] + 0.025 * (right_position + 3)
    xn_max = kn / 100
    xt_max = kt / 100

    if nam == AirMassRegime.MEDIUM:
        xt_max -= 0.025
        xn_max -= 0.050
    elif nam == AirMassRegime.HIGH:
        xt_max -= 0.10
        xn_max -= 0.15

    left_boundary = boundary_from_gompertz_curve(
        int(left_shape), left_position, "left"
    )
    right_boundary = boundary_from_gompertz_curve(
        int(right_shape), right_position, "right"
    )

    global_out, direct_out, diffuse_out = seriqc_flag(
        ghi=ghi,
        dni=dni,
        dhi=dhi,
        zenith=sol_zen,
        ghi_extra=etr,
        dni_extra=etrn,
        airmass=air_mass,
        Kt_max=xt_max,
        Kn_max=xn_max,
        Kd_max=xd_max,
        left_boundary=left_boundary,
        right_boundary=right_boundary,
        **kwargs,
    )
    return (
        global_out,
        direct_out,
        diffuse_out,
        etr,
        etrn,
        sol_zen,
        return_value,
    )
