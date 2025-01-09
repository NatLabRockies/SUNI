# -*- coding: utf-8 -*-
"""SUNI merging functionality"""
from math import sqrt


def system_uncertainty(kt, kn, kd):
    """Compute percent system uncertainty.

    Parameters
    ----------
    kt, kn, kd : int | float
        Kt, Kn, and Kd values to compute uncertainty with.

    Returns
    -------
    float
        Percent system uncertainty.
    """
    return (kt / (kn + kd) - 1) * 100


def merge(
    kt,
    kn,
    kd,
    radiometer_uncertainty_ghi,
    radiometer_uncertainty_dni,
    radiometer_uncertainty_dhi,
):
    """Merge measurement and system uncertainty.

    Parameters
    ----------
    kt, kn, kd : int | float
        Kt, Kn, and Kd values to compute uncertainty with.
    radiometer_uncertainty_ghi : int | float
        Radiometer GHI uncertainty value.
    radiometer_uncertainty_dni : int | float
        Radiometer DNI uncertainty value.
    radiometer_uncertainty_dhi : int | float
        Radiometer DHI uncertainty value.

    Returns
    -------
    u95_ghi, u95_dni, u95_dhi : float
        95th percentile uncertainty for irradiance measurements.
    field_uncertainty, radiometer_uncertainty : float
        Field and instrument uncertainty
    """
    dni_frac = radiometer_uncertainty_dni * kn / (kn + kd)
    dhi_frac = radiometer_uncertainty_dhi * kd / (kn + kd)
    radiometer_uncertainty = _merge_sqrt(
        radiometer_uncertainty_ghi / 2, (dni_frac + dhi_frac) / sqrt(3)
    )

    field_uncertainty = max(
        abs(system_uncertainty(kt, kn, kd)) - radiometer_uncertainty, 0
    )

    u95_ghi = _merge_sqrt(
        radiometer_uncertainty_ghi / 2, field_uncertainty / 2
    )
    u95_dni = _merge_sqrt(
        radiometer_uncertainty_dni / 2, field_uncertainty / 2
    )
    u95_dhi = _merge_sqrt(
        radiometer_uncertainty_dhi / 2, field_uncertainty / 2
    )
    return u95_ghi, u95_dni, u95_dhi, field_uncertainty, radiometer_uncertainty


def _merge_sqrt(val1, val2):
    """Merge two values using sqrt"""
    return 2 * sqrt(val1**2 + val2**2)
