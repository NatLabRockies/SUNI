# fmt: off
"""Functions for determining SERI QC quality control flags."""
import logging

import numpy as np
import matplotlib.path as mpath

from seriqc.utilities import as_c_int


logger = logging.getLogger(__name__)

# Things to consider
# There is adjustments of Kt_max and Kn_max by airmass hard coded in the C-code
# "Max Kt is 0.10 larger than the Gompertz right boundary)"

# Set K-values above 100 to 100?
# Int values are trucated both in C and Python

# Implement this somewhere:
# Strange setting of Kd_max (This should be passed in!)
# Kd_max = [0.19, 0.22, 0.24, 0.28, 0.32][boundary['right_shape']-1]


def seriqc_flag(ghi, dni, dhi, zenith, dni_extra, airmass, Kt_max, Kn_max,
                Kd_max, left_boundary=None, right_boundary=None,
                twilight_zenith=80, nan_threshold=8000,
                min_irradiance=-10, max_nighttime_irradiance=10,
                K_diff_threshold=0.03, ghi_extra=None):
    """Generate SERI-QC flags for one timestamp.

    Parameters
    ----------
    ghi : float
        Global horizontal irradiance in W/m^2.
    dni : float
    zenith : float
        Apparent solar zenith angle in degrees.
    dni_extra : float
        Extraterrestrial normal irradiance in W/m^2.
    airmass : float
        Relative airmass. Can be calculated using:
        py:func:`pvlib.atmosphere.get_relative_airmass`. The
        'kastenyoung1989' model was used by the original software.
    Kt_max : float
        Upper limit of Kt.
    Kn_max : float
        Upper limit of Kn.
    Kd_max : float
        Upper limit of Kd.
    left_boundary : array
        A 2xN array of (Kt, Kn) coordinates describing the left boundary.
    right_boundary : array
        A 2xN array of (Kt, Kn) coordinates describing the right boundary.
    twilight_zenith : numeric, default : 80
        Zenith angle in degrees for when to apply twilight irradiance limits.
    nan_threshold : numerics, default : 8000
        Irradiance values above this limit will be considered as missing / nan.
    min_irradiance : numeric, default : -10
        Lower limit in W/m^2 for irradiance values.
    max_nighttime_irradiance : numerics, default : 10
        Upper limit in W/m^2 for nighttime irradiance values.
    K_diff_threshold : numerics, default : 0.03
        Threshold distance from the K-space boundary zone for when to flag a
        point.
    ghi_extra : float, optional
        Global extraterrestrial irradiance in W/m^2. If not specified,
        this value is computed from the `dni_extra` input using the
        relationship :math:`ghi_extra = dni_extra * cos(zenith)`.
        By default, ``None``.

    Returns
    -------
    ghi_flag : int
        Global horizontal irradiance quality control flag.
    dni_flag : int
        Direct normal irradinace quality control flag.
    dhi_flag : int,
        Diffuse irradinace quality control flag.

    References
    ----------
    [2] F. Kasten and A. T. Young, Revised optical air mass tables and
        approximation formula, Applied Optics, 14 (22), 4735-4738, 1989.
    """
    # The original code first initializes all flags as 0 (untested).
    # ghi_flag = dni_flag = dhi_flag = 0
    # Set all flags to 1 (only one parameter present; passed limits test)
    ghi_flag = dni_flag = dhi_flag = 1

    # Irradiance values exceeding the min_irradiance threshold are set as nan
    if ghi > nan_threshold:
        ghi = np.nan
    if dni > nan_threshold:
        dni = np.nan
    if dhi > nan_threshold:
        dhi = np.nan

    # Missing values are flagged as 99
    if np.isnan(ghi):
        ghi_flag = 99
    if np.isnan(dni):
        dni_flag = 99
    if np.isnan(dhi):
        dhi_flag = 99

    # Nighttime test
    if zenith >= 90:  # Condition could also be expressed as "if ETR=0"
        if ghi < min_irradiance:
            ghi_flag = 7
        elif ghi > max_nighttime_irradiance:
            ghi_flag = 8
        if dni < min_irradiance:
            dni_flag = 7
        elif dni > max_nighttime_irradiance:
            dni_flag = 8
        if dhi < min_irradiance:
            dhi_flag = 7
        elif dhi > max_nighttime_irradiance:
            dhi_flag = 8
        return ghi_flag, dni_flag, dhi_flag

    # Convert irradiance values to K-space
    #
    if ghi_extra is None:
        ghi_extra = dni_extra * np.cos(np.deg2rad(zenith)) + 0.5/100
    Xt = ghi / ghi_extra
    Xn = dni / dni_extra
    Xd = dhi / ghi_extra

    # Intifying the K-space variables (could be removed)
    Kt = as_c_int(Xt*100 + 0.5)/100
    Kn = as_c_int(Xn*100 + 0.5)/100
    Kd = as_c_int(Xd*100 + 0.5)/100

    logger.debug(
        f"    - P - XT: {Xt:.6f}, XN: {Xn:.6f}, KT: {Kt*100:.4f}, "
        f"KN: {Kn*100:.4f}",
    )

    # Daytime tests (one-component limit tets)
    if Xt < 0.05:
        ghi_flag = 7
    elif Xt > Kt_max + 0.10:  # Added 0.10 the original Fortran code, seems silly
        ghi_flag = 8
    if dni < min_irradiance:
        dni_flag = 7
    elif Xn > Kn_max:
        dni_flag = 8
    if Xd < 0.03:
        dhi_flag = 7
    elif Xd > Kd_max:
        dhi_flag = 8

    logger.debug(
        f"    - P - Solzen: {zenith:.6f}, ETR: {ghi_extra:.6f}, "
        f"ETRN {dni_extra:.6f}, XT: {Xt:.6f}, KT: {Xt*100 + 0.5:.6f}, "
        f"XN: {Xn:.6f}, KN: {Xn*100 + 0.5:.6f}, XD: {Xd:.6f}, "
        f"KD: {Xd*100 + 0.5:.6f}, XTmax: {Kt_max:.6f}, XNmax: {Kn_max:.6f}, "
        f"XDmax: {Kd_max:.6f}"
    )

    # Twilight one-component tests (overrules daytime tests)
    # Do not use a flag of 7 if ghi or dhi >= min_irradiance
    # If ETR<=25 W/m, a ghi value of <=10 W/m2 should not be considered to high
    if (zenith > twilight_zenith) & (zenith < 90):
        if (ghi_flag == 7) & (ghi >= min_irradiance):
            ghi_flag = 1
        if (dhi_flag == 7) & (dhi >= min_irradiance):
            dhi_flag = 1
        if (ghi_flag == 8) & (ghi_extra <= 25) & (ghi <= max_nighttime_irradiance):
            ghi_flag = 1
        return ghi_flag, dni_flag, dhi_flag

    # Terminate tests if only one component is present
    components_valid = (ghi_flag == 1) + (dni_flag == 1) + (dhi_flag == 1)
    if components_valid <= 1:
        return ghi_flag, dni_flag, dhi_flag

    # Check whether Kn < Kt
    # If two components pass the one-component tests, they are then compared
    # to determine if Kn > Kt (physically impossible). If Kn > Kt, the tests
    # are terminated with flags that indicate the error.
    if (ghi_flag == 1) & (dni_flag == 1):  # Calculate two-component test
        Khigh = Kn - Kt + 1e-6  # Name taken from C code
        logger.debug(f"KN: {Kn:.6f}, KT: {Kt:.6f}, Khigh: {Khigh}")
        if Khigh >= 0.05:  # Would make more sense to use K_diff_threshold
            if Khigh >= 0.20:
                ghi_flag = 97
                dni_flag = 97
            elif Khigh >= 0.15:
                ghi_flag = 96
                dni_flag = 96
            elif Khigh >= 0.10:
                ghi_flag = 95
                dni_flag = 95
            elif Khigh >= 0.05:
                ghi_flag = 94
                dni_flag = 94
            return ghi_flag, dni_flag, dhi_flag

    # Perform three-parameter test
    if components_valid == 3:
        # SQC_3C(Kt, Kn, Kd, ghi_flag, dni_flag, dhi_flag)
        ghi_flag, dni_flag, dhi_flag = \
            SQC_3C(Kt, Kn, Kd, K_diff_threshold=0.03)
        # Return flags if 3-component test failed
        if ghi_flag > 3:  # Note flag == 3 means three-component test passed
            return ghi_flag, dni_flag, dhi_flag

    # Perform two-component test
    if (ghi_flag <= 3) & (dni_flag <= 3):
        ghi_flag, dni_flag = SQC_2C(
            Kt, Kn, Kt_max, Kn_max, left_boundary, right_boundary,
            K_diff_threshold=K_diff_threshold)
        # ARJ don't really understand the purpose of this line
        if dhi_flag != 3:
            return ghi_flag, dni_flag, dhi_flag

        # If the 2-parameter test returned a flag of greater than 5%, all flags
        # should be 9. Otherwise, return 3's.
        if ghi_flag > 21:
            ghi_flag = dni_flag = dhi_flag = 9
        else:
            ghi_flag = dni_flag = 3
        return ghi_flag, dni_flag, dhi_flag

    # This section is only reached if either ghi or dni is missing
    if ghi_flag == 1:
        # DNI must be missing, and Kn is calculated from GHI and DHI
        Kn_calc = Kt - Kd + 1e-6
        # SQC_2C(Kt, Kn_calc, ghi_flag, dhi_flag, Il, Ir, Jl, Jr,Kt_max,Kn_max)
        ghi_flag, dhi_flag = SQC_2C(
            Kt, Kn_calc, Kt_max, Kn_max, left_boundary, right_boundary,
            K_diff_threshold=K_diff_threshold)
    else:
        # GHI must be missing, and Kt is calculated from DNI and DHI
        Kt_calc = Kn + Kd + 1e-6
        # SQC_2C(Kt_calc, Kn, dhi_flag, dni_flag, Il, Ir, Jl, Jr,Kt_max,Kn_max)
        dhi_flag, dni_flag = SQC_2C(
            Kt_calc, Kn, Kt_max, Kn_max, left_boundary, right_boundary,
            K_diff_threshold=K_diff_threshold)
        dhi_flag = dni_flag  # Why is this flag set?
    # ARJ: The below return is not present in the C-code but seems necessary...
    return ghi_flag, dni_flag, dhi_flag


def SQC_3C(Kt, Kn, Kd, K_diff_threshold=0.03):
    """
    Derive three-component SERI-QC quality flags.

    The quality flags are assigned based on the deviations from the closure
    equation in the K-space (Kt = Kn + Kd).

    The returned flags may be either 3 (internally consistent) or in the range
    of 10-93, depdening on whether the individual parameter is to high or low,
    and the magnitude of the error. The percentage error can be inferred from
    the flag value.

    Parameters
    ----------
    Kt : numeric
        DESCRIPTION.
    Kn : numeric
        DESCRIPTION.
    Kd : numeric
        DESCRIPTION.
    K_diff_threshold : numeric, default : 0.03
        Tolerance of consistency among the K-values, fraction. Original
        SERI QC software used 0.03 (3%).

    Returns
    -------
    ghi_flag_3 : int
        Global horizontal irradiance three-component quality control flag.
    dni_flag_3 : int
        Direct normal irradinace three-component quality control flag.
    dhi_flag_3 : int,
        Diffuse irradinace three-component quality control flag.

    Notes
    -----
    The K-value input parameters are required to be fractions, whereas the
    original SERI QC function assumed integer percentages.
    """
    # Performs 3-component checking for SERI_QC1
    # Based on deviations from closure equation (Kt = Kn + Kd)

    # Initialize all flags as succesfull (3)
    ghi_flag_3 = dni_flag_3 = dhi_flag_3 = 3
    K_diff = Kn + Kd - Kt
    sign = int(np.sign(K_diff))
    # Modified the line below to match with the original code which
    # expressed the K-values as percentage integers.
    # PP: Added the 1e-3 adder to fix floating point precision differences
    K_diff_abs = int(100*abs(K_diff) + 1e-3)
    # The IQC0 and IQC1 variables are intermediary and follows the name from
    # the original SERI QC C code.
    IQC0 = 4 * min(K_diff_abs, 23) - 1
    if (sign == 1):
        IQC0 = IQC0 - 1
    # IQC1 has to take on the opposite sign (TOO HIGH/TOO LOW) from IQC0
    IQC1 = IQC0 + sign
    if K_diff_abs >= 3:
        ghi_flag_3 = IQC0
        dni_flag_3 = IQC1
        dhi_flag_3 = IQC1
    return ghi_flag_3, dni_flag_3, dhi_flag_3


def SQC_2C(Kt, Kn, Kt_max, Kn_max, left_boundary, right_boundary,
           K_diff_threshold=0.03):
    """
    Derive two-component SERI QC quality flags.

    The position of KT and KN is evaluated against the selected Gompertz curves
    and the flags IQCglo and IQCdir are evaluated.

    Parameters
    ----------
    Kt : numeric
        DESCRIPTION.
    Kn : numeric
        DESCRIPTION.
    Kt_max : numeric
        The maximum allowable Kt.
    Kn_max : numeric
        The maximum allowable Kn.

    Returns
    -------
    ghi_flag : int
        Global horizontal irradiance quality control flag.
    dni_flag : int
        Direct normal irradinace quality control flag.

    Notes
    -----
    Curve(I,J,K) are:
    I: 0 if the left boundary, 1 if the right.
    J: Curve type. When I is 1, J spans 1 to 6 and when I is 2, J spans 1 to 5.
    K: K-value. If L < 1, L is reassigned to 1. If K > 1, K is reassigned to 1.
       This is because such values are both meaningless and troublesome for the
       Gompertz function.
    """
    # Initialize flags as succesfull (2)
    ghi_flag = dni_flag = 2

    # All the following equations assumes the K-values are integer percentages
    Kn = int(Kn*100 + 1e-6)
    Kt = int(Kt*100 + 1e-6)
    Kn_max = int(Kn_max*100 + 0.51)
    Kt_max = int(Kt_max*100 + 0.51)
    K_diff_threshold = K_diff_threshold*100

    Xt_left, Xn_left = left_boundary*100
    Xt_right, Xn_right = right_boundary*100

    # Top_L, Bot_L, Top_R, and Bot_R are the Kn values of the boundaries
    Top_L = Xt_left[Kn_max-1]
    Top_L = max(Top_L, 0)
    Top_L = min(Top_L, Kt_max)

    Bot_L = Xt_left[1-1]
    Bot_L = max(Bot_L, 0.0)
    Bot_L = min(Bot_L, Kt_max)

    Top_R = Xt_right[Kn_max-1]
    Top_R = max(Top_R, 0.0)
    Top_R = min(Top_R, Kt_max)

    Bot_R = Xt_right[1-1]
    Bot_R = max(Bot_R, 0)
    Bot_R = min(Bot_R, Kt_max)

    # All points on the Gompertz curve are described by arrays Xn and Xt
    # Left curve is cut off when Kn_max is met, hence [:Kn_max]
    Xn_left = Xn_left[:Kn_max]
    Xt_left = Xt_left[:Kn_max]
    dist_left = np.round(
        np.sqrt((Kt - np.maximum(Xt_left, 1))**2 + (Kn - Xn_left)**2),
        decimals=12  # sqrt sometimes gives .9999 out to 13 decimals
    )
    # Right curve is cut off when Kt_max is met (have to calculate cutoff Kn)
    N_right_max = np.argmax(Kt_max < Xt_right)  # index of cutoff
    Xt_right = Xt_right[:N_right_max]
    Xn_right = Xn_right[:N_right_max]

    boundary_vertices_x = [
        Xt_left[0], Xt_left, Top_L, Top_R, Kt_max, Xt_right[::-1], Xt_right[0]
    ]
    boundary_vertices_y = [
        0, Xn_left, Kn_max, Kn_max, Xn_right[-1], Xn_right[::-1], 0
    ]

    boundary_vertices_x = np.hstack(boundary_vertices_x)
    boundary_vertices_y = np.hstack(boundary_vertices_y)
    boundary_vertices_x[boundary_vertices_x < 0] = 0
    boundary_vertices_y[boundary_vertices_y < 0] = 0
    boundary_vertices = np.vstack([boundary_vertices_x, boundary_vertices_y]).T
    point_within_boundary = is_point_within_boundary(
        (Kt, Kn), boundary_vertices)
    if point_within_boundary:
        return ghi_flag, dni_flag

    # If Kn is negative or greater than Kn_max, but Kt lies within the Gompertz
    # bounds, we should measure the vertical distance only.
    # Kn is above Kn_max and within the Gompertz curves
    if (Kn > Kn_max) & (Kt <= Top_R) & (Kt >= Top_L):
        IQC = Kn - Kn_max
        if IQC >= K_diff_threshold:
            ghi_flag = 4 * min(IQC, 23)
            dni_flag = ghi_flag + 1
        return ghi_flag, dni_flag
    # Kn is above Kn_max, and Kt is to the right of Gompertz curve cutoff
    elif (Kn > Kn_max) & (Kt > Top_R):
        IQC = int(np.sqrt((Kn-Kn_max)**2 + (Kt-Top_R)**2))
        if IQC >= K_diff_threshold:
            dni_flag = 4 * min(IQC, 23)
            ghi_flag = dni_flag + 1
        return ghi_flag, dni_flag
    # Kn is below zero and Kt is outside Gompertz curve
    elif (Kn < 0) & (Kt <= Bot_R) & (Kt >= Bot_L):
        IQC = -Kn
        if IQC >= K_diff_threshold:
            dni_flag = 4 * min(IQC, 23)
            ghi_flag = dni_flag + 1
        return ghi_flag, dni_flag
    # Kn is below zero and Kt is to the left of Gompertz curve
    elif (Kn < 0) & (Kt < Bot_L):
        # ARJ added conversion to integer
        IQC = int(np.sqrt(Kn**2 + (Kt-Bot_L)**2))
        if IQC >= K_diff_threshold:
            ghi_flag = 4 * min(IQC, 23)
            dni_flag = ghi_flag + 1
        return ghi_flag, dni_flag

    # The below implementation checks distance to all Gompertz curves
    # Calculate minimum distance
    dist_right = np.round(
        np.sqrt((Kt - np.maximum(Xt_right, 1))**2 + (Kn - Xn_right)**2),
        decimals=12  # sqrt sometimes gives .9999 out to 13 decimals
    )
    min_dist_left = min(dist_left)
    min_dist_right = min(dist_right)
    min_dist = min(min_dist_left, min_dist_right)
    # Special case of point below Kn_max and directly to the right of Kt_max
    if (Kt > Kt_max) & (Kn > Xn_right[-1]):
        min_dist = Kt - Kt_max
        min_dist_right = min_dist
    # CHECK: If Kn is below 0, that counts as "to the right".
    # CHECK: If Kn is above KNmax, that counts as "to the left".
    # if (( Xt >= Kt2 ) && ( Kn2 >= 0.0 )) return(-1);
    if min_dist >= K_diff_threshold:
        Iflg = int(min_dist)
        IQClo = 4 * min(Iflg, 23)
        IQChi = IQClo + 1
        if min_dist_right > min_dist_left:  # To the left of Gompertz curve
            # Code strucure from original SERI QC
            # The distance is large enough to trigger a 2-component flag.
            if Iflg >= 3:
                dni_flag = max(IQChi, dni_flag)
                ghi_flag = max(IQClo, ghi_flag)
            return ghi_flag, dni_flag
        else:  # to the right of Gompertz curve
            if Iflg >= 3:
                dni_flag = max(IQClo, dni_flag)
                ghi_flag = max(IQChi, ghi_flag)

    return ghi_flag, dni_flag


def is_point_within_boundary(point, boundary_vertices):
    """
    Determine if point is within boundary.

    Parameters
    ----------
    point : tuple
        THe point (x, y) to check.
    boundary_vertices : array-like
        An Nx2 float array of vertices.

    Returns
    -------
    within_boundary : boolean
        Whether the point is within the boundary.
    """
    boundary_path = mpath.Path(boundary_vertices)
    # A small negative radius ensures that points on the boundary are counted
    # as within the boundary.
    return boundary_path.contains_point(point, radius=-0.001)
