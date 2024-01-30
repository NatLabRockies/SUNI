from math import sqrt


def system_uncertainty(kt, kn, kd):
    return (kt / (kn + kd) - 1) * 100


def merge(
    kt,
    kn,
    kd,
    radiometer_uncertainty_ghi,
    radiometer_uncertainty_dni,
    radiometer_uncertainty_dhi,
):
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
    return 2 * sqrt(val1**2 + val2**2)
