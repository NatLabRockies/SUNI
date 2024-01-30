"""Test the seriqc two-component test function."""
import logging
import os
import pytest
from ctypes import cdll, c_char_p, c_int, c_double, byref
from pathlib import Path

import numpy as np

import seriqc
from seriqc.exec import seriqc_from_file
from seriqc import SQC_2C


SERIQC_DIR = Path(__file__).parent.parent.parent
DLL = SERIQC_DIR / "c_code" / "SERIQC.dll"
pytestmark = pytest.mark.skipif(
    condition=not DLL.exists(), reason="C code has not been compiled"
)
logger = logging.getLogger("seriqc")


@pytest.fixture(scope="module")
def seriqc_lib():
    return cdll.LoadLibrary(DLL.as_posix())


@pytest.fixture(autouse=True)
def c_code_alignment(monkeypatch):
    """Align some function implementations with C code implementations"""

    monkeypatch.setattr(
        seriqc.utilities,
        "conform_to_spa_years",
        seriqc.utilities.conform_to_solpos_years,
        raising=True,
    )
    monkeypatch.setattr(
        seriqc.exec,
        "conform_to_spa_years",
        seriqc.utilities.conform_to_solpos_years,
        raising=True,
    )


def assert_python_matches_c(
    seriqc_lib,
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
    check_flags=True,
    truth_value=None,
):
    """Assert that Python code outputs match C code outputs for given inputs"""
    c_site = bytes(site, "utf-8")
    c_qc0_dir = bytes("".join([str(qc0_dir), os.sep]), "utf-8")

    IQCglo = c_int(-1)
    IQCdir = c_int(-1)
    IQCdif = c_int(-1)

    truth = seriqc_lib.seri_qc1(
        c_char_p(c_site),
        c_char_p(c_qc0_dir),
        year,
        month,
        day,
        hour,
        minute,
        interval,
        c_double(ghi),
        c_double(dni),
        c_double(dhi),
        byref(IQCglo),
        byref(IQCdir),
        byref(IQCdif),
    )
    truth_flags = [IQCglo.value, IQCdir.value, IQCdif.value]
    ghi_flag, dni_flag, dhi_flag, *__, return_code = seriqc_from_file(
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
        pressure=820,
        temp=11,
    )

    logger.debug(f"Val: {return_code} Truth: {truth}")
    logger.debug(f"Python: {(ghi_flag, dni_flag, dhi_flag)} C: {truth_flags}")

    assert return_code == truth, f"Val: {return_code} Truth: {truth}"
    if truth_value is not None:
        assert return_code == truth_value

    if check_flags:
        err_str = f"Python: {(ghi_flag, dni_flag, dhi_flag)} C: {truth_flags}"
        assert [ghi_flag, dni_flag, dhi_flag] == truth_flags, err_str


def assert_python_matches_c_SQC_2C(
    seriqc_lib,
    bms_january_1min_boundaries,
    Kt,
    Kn,
):
    """Assert that Python code outputs match C code outputs for given inputs"""
    left_boundary, right_boundary, *K_max_vals = bms_january_1min_boundaries
    Kt_max, Kn_max, __ = K_max_vals

    ghi_flag_2, dni_flag_2 = SQC_2C(
        Kt=Kt,
        Kn=Kn,
        Kt_max=Kt_max,
        Kn_max=Kn_max,
        left_boundary=left_boundary,
        right_boundary=right_boundary,
        K_diff_threshold=0.03,
    )

    IQCt2 = c_int(-1)
    IQCn2 = c_int(-1)

    seriqc_lib.SQC_2C(
        c_int(int(Kt * 100 + 1e-6)),
        c_int(int(Kn * 100 + 1e-6)),
        byref(IQCt2),
        byref(IQCn2),
        4,
        1,
        1,
        14,
        c_int(int(Kt_max * 100)),
        c_int(int(Kn_max * 100)),
    )

    np.testing.assert_equal(ghi_flag_2, IQCt2.value)
    np.testing.assert_equal(dni_flag_2, IQCn2.value)


def test_dll(seriqc_lib, test_data_dir):
    """A "meta" test to ensure DLL we test against gives reasonable values."""

    data_dir = "".join([str(test_data_dir), os.sep])
    site, qc0_dir = b"BMS", bytes(data_dir, "utf-8")

    ghi = c_double(4500)
    dni = c_double(4500)
    dhi = c_double(9000)

    IQCglo = c_int(-1)
    IQCdir = c_int(-1)
    IQCdif = c_int(-1)

    retval = seriqc_lib.seri_qc1(
        c_char_p(site),
        c_char_p(qc0_dir),
        2000,
        1,
        1,
        1,
        1,
        60,
        ghi,
        dni,
        dhi,
        byref(IQCglo),
        byref(IQCdir),
        byref(IQCdif),
    )

    assert retval == 0
    assert IQCglo.value == 8
    assert IQCdir.value == 8
    assert IQCdif.value == 99


@pytest.mark.parametrize(
    "time",
    [
        (1, 1, 1, 1, 1),
        (0, 1, 1, 1, 1),
        (1, 1, 1, 1, 1),
        (12, 1, 1, 1, 1),
        (13, 1, 1, 1, 1),
        (1, 0, 1, 1, 1),
        (1, 1, 1, 1, 1),
        (1, 31, 1, 1, 1),
        (1, 32, 1, 1, 1),
        (1, 1, 0, 1, 1),
        (1, 1, 24, 0, 1),
        (1, 1, 25, 0, 1),
        (1, 1, 1, -1, 1),
        (1, 1, 1, 0, 1),
        (1, 1, 1, 59, 1),
        (1, 1, 1, 60, 1),
        (1, 1, 0, -1, 1),
        (1, 1, 0, 0, 1),
        (1, 1, 24, 0, 1),
        (1, 1, 24, 1, 1),
        (1, 1, 1, 1, 0),
        (1, 1, 1, 1, 1),
        (1, 1, 1, 1, 60),
        (1, 1, 1, 1, 61),
        (0, 0, -1, -1, 0),
        (1, 0, -1, -1, 0),
        (1, 1, -1, -1, 0),
        (0, 1, -1, -1, 0),
        (0, 0, 1, 1, 1),
    ],
)
def test_time_validation(seriqc_lib, test_data_dir, time):
    """Test time validation of python to C code"""

    month, day, hour, minute, interval = time
    year = 2000
    ghi = dni = 4500
    dhi = 9000
    site = "BMS"

    assert_python_matches_c(
        seriqc_lib,
        site,
        test_data_dir,
        year,
        month,
        day,
        hour,
        minute,
        interval,
        ghi,
        dni,
        dhi,
    )


def test_dne_file(seriqc_lib, test_data_dir, tmp_path):
    """Test that python and c code returns the same code for DNE Qc0 file"""

    month = day = hour = minute = interval = 1
    year = 2000
    ghi = dni = 4500
    dhi = 9000

    assert_python_matches_c(
        seriqc_lib,
        "      ",
        test_data_dir,
        year,
        month,
        day,
        hour,
        minute,
        interval,
        ghi,
        dni,
        dhi,
        truth_value=1,
    )

    month = 3
    assert_python_matches_c(
        seriqc_lib,
        "BMS",
        tmp_path,
        year,
        month,
        day,
        hour,
        minute,
        interval,
        ghi,
        dni,
        dhi,
        truth_value=128,
    )


def test_bad_file_input(seriqc_lib, test_data_dir, tmp_path):
    """Test that python and c code returns the same code for bad QC0 file"""

    day = hour = minute = interval = 1
    month = 2
    year = 2000
    ghi = dni = 4500
    dhi = 9000
    site = "BMS"

    with open(test_data_dir / "s_BMS.qc0", "r") as fh:
        lines = fh.readlines()

    lines[10] = lines[10].replace("FEB", "DNE")
    with open(tmp_path / "s_BMS.qc0", "w") as fh:
        fh.writelines(lines)

    assert_python_matches_c(
        seriqc_lib,
        site,
        tmp_path,
        year,
        month,
        day,
        hour,
        minute,
        interval,
        ghi,
        dni,
        dhi,
        truth_value=256,
    )


def test_bad_kt_kn_input(seriqc_lib, test_data_dir, tmp_path):
    """Test that python and c code returns the same code for bad Kt/Kn input"""

    day = minute = interval = 1
    month = 5
    hour = 12
    year = 2000
    ghi = dni = 4500
    dhi = 9000
    site = "BMS"

    with open(test_data_dir / "s_BMS.qc0", "r") as fh:
        lines = fh.readlines()

    lines[13] = lines[13].replace("83-95/95/00/00;", "00-00/00/00/00")
    with open(tmp_path / "s_BMS.qc0", "w") as fh:
        fh.writelines(lines)

    assert_python_matches_c(
        seriqc_lib,
        site,
        tmp_path,
        year,
        month,
        day,
        hour,
        minute,
        interval,
        ghi,
        dni,
        dhi,
        check_flags=False,
        truth_value=6144,
    )


def test_bad_curve_input(seriqc_lib, test_data_dir, tmp_path):
    """Test that python and c code returns the same code for bad curve input"""

    day = minute = interval = 1
    month = 4
    hour = 12
    year = 2000
    ghi = dni = 4500
    dhi = 9000
    site = "BMS"

    with open(test_data_dir / "s_BMS.qc0", "r") as fh:
        lines = fh.readlines()

    lines[12] = lines[12].replace("4-10 1-15/15/00/00", "0-00 0-00/00/00/00")
    with open(tmp_path / "s_BMS.qc0", "w") as fh:
        fh.writelines(lines)

    assert_python_matches_c(
        seriqc_lib,
        site,
        tmp_path,
        year,
        month,
        day,
        hour,
        minute,
        interval,
        ghi,
        dni,
        dhi,
        check_flags=False,
        truth_value=1536,
    )


@pytest.mark.parametrize(
    "hour, ghi, dni, dhi",
    [
        (1, -20, -20, -20),
        (0, 100, 100, 100),
        (12, 200, 400, 94),
        (12, 160, 400, 95),
        (12, 100, 400, 96),
        (12, 80, 400, 97),
        (12, 417, 105, 417 - 100 * np.cos(np.deg2rad(62.85))),
        (12, 400, 500, 400 - 500 * np.cos(np.deg2rad(62.85))),
        (12, 9000, 100, 400 - 100 * np.cos(np.deg2rad(62.85))),
        (12, 400, 9000, 400 - 500 * np.cos(np.deg2rad(62.85))),
        (12, 200, 400, 9000),
        (12, 160, 400, 9000),
        (12, 100, 400, 9000),
        (12, 80, 400, 9000),
        (12, 9, 9000, 9000),
        (12, 1, 9000, 1),
        (12, 4500, 4500, 4500),
        (12, 9000, 4500, 4500),
        (12, 4500, 9000, 4500),
        (12, 4500, 4500, 9000),
        (12, 9000, 9000, 9000),
        (7, 1, 9000, 1),
        (7, 9, 9000, 9000),
        (12, 9000, 1020, 140),
        (12, 4.723, 9000, 9000),
        (12, 9000, -11, 9000),
        (12, 9000, -11, -1.166),
        (12, 133, 413, 9000),
        (12, 106, 413, 9000),
        (12, 66, 413, 9000),
        (12, 53, 413, 9000),
        (8, 0.1, 9000, 0.1),
        (7, 0.0083978, 9000, 9000),
    ],
)
def test_nominal_exec(seriqc_lib, test_data_dir, ghi, dni, dhi, hour):
    """Test a nominal run"""

    year, month, interval = 2000, 1, 60
    if hour:
        minute = 30
        day = 1
    else:
        minute = 30
        day = 2
    site = "BMS"

    assert_python_matches_c(
        seriqc_lib,
        site,
        test_data_dir,
        year,
        month,
        day,
        hour,
        minute,
        interval,
        ghi,
        dni,
        dhi,
    )


def test_nominal_time_edge_cases(seriqc_lib, test_data_dir):
    """Test a nominal run with time edge cases"""

    year, month, day, minute, interval = 0, 1, 1, 1, 60
    hour, ghi, dni, dhi = 0, 400, 500, 400 - 500 * np.cos(np.deg2rad(62.85))
    site = "BMS"

    assert_python_matches_c(
        seriqc_lib,
        site,
        test_data_dir,
        year,
        month,
        day,
        hour,
        minute,
        interval,
        ghi,
        dni,
        dhi,
    )


# Run this test using:
# pytest --log-cli-level=DEBUG test_seriqc_against_c_code.py -k test_nominal_benchmarking_exec -rapP
@pytest.mark.parametrize(
    "interval, year, month, day, hour, minute, ghi, dni, dhi, site",
    [
        (1, 2021, 1, 1, 7, 25, 3.4753, 0.225650, 4.10509, "NRELSR"),
        (1, 2021, 1, 1, 7, 26, 3.9072, 0.251888, 4.50005, "NRELSR"),
        (1, 2021, 1, 1, 8, 32, 105.179, 0.377831, 105.89, "NRELSR"),
        (1, 2021, 1, 1, 11, 24, 338.072, 126.07, 265.142, "NRELSR"),
        (1, 2021, 1, 3, 15, 5, 18.083, 0.215152, 18.5682, "NRELSR"),
        (1, 2021, 1, 10, 9, 9, 213.496, 277.277, 156.698, "NRELSR"),
        (1, 2021, 1, 10, 9, 12, 244.159, 298.688, 149.258, "NRELSR"),
        (1, 2021, 1, 10, 9, 14, 236.727, 231.391, 152.035, "NRELSR"),
        (1, 2021, 1, 10, 9, 16, 237.137, 173.43, 149.798, "NRELSR"),
        (1, 2021, 1, 10, 9, 45, 270.915, 309.846, 183.669, "NRELSR"),
        (1, 2021, 1, 24, 12, 31, 804.681, 884.924, 346.868, "NRELSR"),
        (5, 1987, 1, 1, 4, 0, -2.3914, 0.48698, -99999, "NRELSR"),
        (5, 1987, 1, 1, 4, 0, -2.3914, 0.48698, 99999, "NRELSR"),
        (5, 1987, 1, 7, 12, 10, 284.03, 681.75, 99999, "NRELSR"),
        (5, 1987, 1, 7, 12, 15, 304.54, 697.9, 99999, "NRELSR"),
        (5, 1987, 1, 7, 12, 20, 355.79, 669.63, 99999, "NRELSR"),
        (5, 1987, 2, 5, 16, 25, 131.64, 730.4, 99999, "NRELSR"),
        (5, 1987, 2, 13, 8, 0, 140.25, 718.63, 99999, "NRELSR"),
        (60, 1987, 2, 12, 9, 0, 234.63, 824.0483, 99999, "NRELSR"),
        (1, 2007, 8, 25, 5, 24, 3.8344, -0.19891, 1.4201, "BOUNDARY1"),
        (1, 2007, 8, 25, 0, 31, -1.4713, -0.153, -3.6025, "BADFORMAT"),
        (1, 2007, 8, 26, 18, 14, 24.327, 112.37, 13.232, "CLOCK"),
        (1, 2007, 8, 26, 18, 15, 18.584, 58.572, 9.5143, "CLOCK"),
        (1, 2007, 8, 26, 18, 16, 13.367, 8.1171, 6.814, "CLOCK"),
        (1, 2007, 8, 30, 18, 10, 25.423, 104.36, 15.348, "CLOCK"),
        (1, 2007, 8, 30, 18, 11, 19.948, 49.52, 11.518, "CLOCK"),
        (1, 2007, 8, 30, 18, 12, 20.518, 64.537, 11.012, "CLOCK"),
        (1, 2007, 8, 30, 18, 13, 26.823, 153.0, 13.99, "CLOCK"),
        (1, 2007, 9, 1, 18, 12, 24.291, 133.33, 10.563, "CLOCK"),
        (1, 2007, 9, 1, 18, 13, 19.119, 85.724, 7.6013, "CLOCK"),
        (1, 2007, 9, 1, 18, 14, 15.49, 41.068, 5.7726, "CLOCK"),
        (5, 1987, 11, 7, 12, 40, 360.27, -10.162, 221.31, "NRELSR"),
        (5, 1987, 11, 7, 12, 45, 350.90, -9.3347, 215.93, "NRELSR"),
        (5, 1987, 11, 7, 12, 50, 317.50, -8.8078, 191.42, "NRELSR"),
        (5, 1987, 11, 7, 12, 55, 327.69, -7.1125, 203.33, "NRELSR"),
        (5, 1987, 11, 7, 13, 00, 433.15, -6.472, 277.07, "NRELSR"),
        (1, 2021, 1, 25, 13, 54, 465.163, 548.49, 227.984, "NRELSR"),
        (5, 1987, 1, 11, 11, 15, 454.39, 976.92, 99999, "NRELSR"),
        (60, 1987, 6, 16, 8, 0, 484.7317, 0, 99999, "NRELSR"),
        (5, 1987, 5, 25, 6, 45, 324.12, 772.13, 99999, "NRELSR"),
        (5, 1987, 5, 25, 6, 50, 340.12, 783.18, 99999, "NRELSR"),
        (5, 1987, 5, 25, 6, 55, 353.5, 790.07, 99999, "NRELSR"),
        (5, 1987, 10, 6, 6, 0, 0.91733, -0.75458, -1.3517, "NRELSR"),
        (5, 1987, 10, 6, 6, 5, 3.2309, 4.3245, 1.1525, "NRELSR"),
        (5, 1987, 10, 6, 6, 10, 6.7789, 43.084, 3.9555, "NRELSR"),
        (5, 1987, 12, 7, 8, 45, 210.14, 800.35, 220.0, "NRELSR"),
        (5, 1987, 12, 7, 8, 50, 222.33, 791.57, 214.35, "NRELSR"),
        (5, 1987, 12, 7, 8, 55, 235.73, 824.89, 102.64, "NRELSR"),
        (15, 1987, 7, 8, 17, 0, 447.09, 690.97, 436.29, "NRELSR"),
        (15, 1987, 7, 8, 17, 5, 381.02, 471.9, 368.25, "NRELSR"),
        (15, 1987, 7, 8, 17, 10, 528.7, 773.62, 525.02, "NRELSR"),
        (15, 1987, 12, 21, 14, 5, 357.73, 941.65, 350.09, "NRELSR"),
        (15, 1987, 12, 21, 14, 10, 340.32, 908.83, 332.79, "NRELSR"),
        (15, 1987, 12, 21, 14, 15, 319.34, 860.13, 311.5, "NRELSR"),
        (60, 1987, 6, 17, 17, 0, 448.3367, -3.3789, 429.1067, "NRELSR"),
        (60, 1987, 6, 17, 18, 0, 253.2683, -2.059, 239.5592, "NRELSR"),
        (60, 1987, 6, 17, 19, 0, 106.046, -2.423, 96.5712, "NRELSR"),
        (1, 2004, 2, 16, 15, 50, 340.1418, 892.48, 78.608, "NRELSR"),
        (1, 2004, 2, 16, 15, 51, 298.9653, 749.54, 80.659, "NRELSR"),
        (1, 2004, 2, 16, 15, 52, 317.0785, 819.52, 80.705, "NRELSR"),
        (1, 2007, 8, 17, 9, 19, 634.91, 704.37, 114.8466, "NRELSR"),
        (1, 2007, 8, 17, 9, 20, 619.84, 682.56, 113.9026, "NRELSR"),
        (1, 2007, 8, 17, 9, 21, 675.27, 754.12, 114.8286, "NRELSR"),
        (1, 2007, 8, 31, 5, 28, 4.4324, -0.15302, 2.9402, "BOUNDARY1"),
        (1, 2007, 8, 31, 5, 29, 5.5383, -0.16067, 4.176, "BOUNDARY1"),
        (1, 2007, 8, 31, 5, 30, 6.5014, -0.15302, 5.1852, "BOUNDARY1"),
        (1, 2007, 8, 31, 6, 29, 148.74, 545.21, 57.7607, "CLOCK"),
        (1, 2007, 8, 31, 6, 30, 152.36, 550.04, 58.5898, "CLOCK"),
        (1, 2007, 8, 31, 6, 31, 155.96, 554.8, 59.7013, "CLOCK"),
        (30, 1987, 5, 25, 8, 0, 468.5083, 788.0733, 99999, "NRELSR"),
        (15, 1987, 2, 7, 16, 20, 145.88, 692.11, 99999, "NRELSR"),
        (15, 1987, 3, 5, 16, 25, 225.45, 637.34, 99999, "NRELSR"),
        (15, 1987, 5, 7, 16, 25, 423.48, 794.7, 99999, "NRELSR"),
        (15, 1987, 12, 20, 14, 50, 250.76, 838.24, 236.99, "NRELSR"),
        (15, 1987, 12, 21, 13, 50, 390.49, 973.79, 381.14, "NRELSR"),
        (5, 1987, 1, 17, 15, 35, 194.58, 831.85, 99999, "NRELSR"),
        (5, 1987, 4, 14, 17, 15, 94.52, 187.3, 99999, "NRELSR"),
        (5, 1987, 5, 18, 17, 15, 398.6, 784.57, 99999, "NRELSR"),
        (5, 1987, 10, 20, 13, 0, 604.51, 913.65, 76.705, "NRELSR"),
        (5, 1987, 12, 2, 9, 5, 255.58, 829.1, 248.72, "NRELSR"),
        (5, 1987, 12, 29, 9, 50, 343.29, 972.18, 324.1, "NRELSR"),
        (1, 2004, 1, 1, 10, 17, 445.544, 735.72, 175.16, "NRELSR"),
        (1, 2004, 1, 1, 10, 18, 463.0384, 788.51, 173.91, "NRELSR"),
        (1, 2004, 1, 1, 10, 19, 431.4529, 696.34, 173.66, "NRELSR"),
        (1, 2004, 6, 19, 13, 9, 788.0905, 396.54, 282.01, "NRELSR"),
        (1, 2004, 6, 19, 13, 10, 985.746, 539.55, 291.56, "NRELSR"),
        (1, 2004, 6, 19, 13, 11, 1066.6223, 615.13, 285.25, "NRELSR"),
        (1, 2004, 6, 28, 7, 19, 282.596, 52.942, 261.26, "NRELSR"),
        (1, 2004, 6, 28, 7, 20, 344.9795, 150.73, 257.6, "NRELSR"),
        (1, 2004, 6, 28, 7, 21, 416.8273, 311.56, 257.17, "NRELSR"),
        (5, 1987, 7, 6, 10, 50, 944.52, 972.73, 86.936, "NRELSR"),
        (5, 1987, 7, 6, 10, 55, 968.82, 996.18, 85.644, "NRELSR"),
        (5, 1987, 7, 6, 11, 0, 978.44, 992.52, 92.242, "NRELSR"),
        (5, 1987, 9, 20, 12, 10, 829.91, 972.64, 89.191, "NRELSR"),
        (5, 1987, 9, 20, 12, 15, 828.11, 971.46, 90.989, "NRELSR"),
        (5, 1987, 9, 20, 12, 20, 828.98, 959.35, 100.29, "NRELSR"),
        (5, 1987, 12, 29, 9, 50, 343.29, 972.18, 324.1, "NRELSR"),
        (1, 2004, 6, 5, 11, 6, 1007.8812, 947.39, 86.289, "NRELSR"),
        (5, 1987, 2, 5, 15, 55, 224.39, 846.12, 99999, "NRELSR"),
    ],
)
def test_nominal_benchmarking_exec(
    seriqc_lib,
    test_data_dir,
    interval,
    year,
    month,
    day,
    hour,
    minute,
    ghi,
    dni,
    dhi,
    site,
):
    """Spot test nominal run cases"""

    assert_python_matches_c(
        seriqc_lib,
        site,
        test_data_dir,
        year,
        month,
        day,
        hour,
        minute,
        interval,
        ghi,
        dni,
        dhi,
    )


@pytest.mark.parametrize(
    "year, month, day, hour, minute",
    [
        (0, 1, 1, 0, 0),
        (0, 1, 2, 0, 0),
        (1948, 3, 1, 0, 0),
        (51, 3, 1, 8, 32),
        (1948, 3, 1, 8, 32),
        (1949, 3, 1, 8, 32),
        (2051, 3, 1, 8, 32),
        (2052, 3, 1, 8, 32),
    ],
)
def test_oob_time(seriqc_lib, test_data_dir, year, month, day, hour, minute):
    """Test a nominal run"""

    ghi, dni, dhi = 105.179, 0.377831, 105.89
    interval = 1
    site = "NRELSR"

    assert_python_matches_c(
        seriqc_lib,
        site,
        test_data_dir,
        year,
        month,
        day,
        hour,
        minute,
        interval,
        ghi,
        dni,
        dhi,
    )


def test_SQC_2C_component_test_correct(
    seriqc_lib, bms_january_1min_boundaries
):
    """Nominal SQC_2C test"""
    assert_python_matches_c_SQC_2C(
        seriqc_lib,
        bms_january_1min_boundaries,
        Kt=0.5,
        Kn=0.4,
    )


def test_SQC_2C_component_test_correct_on_boundary(
    seriqc_lib, bms_january_1min_boundaries
):
    """Test that flag is correctly set to 2, for a point on the boundary"""

    assert_python_matches_c_SQC_2C(
        seriqc_lib,
        bms_january_1min_boundaries,
        Kt=0.2,
        Kn=0.01,
    )


def test_SQC_2C_component_test_correct_max_Kn(
    seriqc_lib, bms_january_1min_boundaries
):
    """Test that flag is correctly set to 2, for a point on the boundary"""
    *__, Kn_max, __ = bms_january_1min_boundaries

    assert_python_matches_c_SQC_2C(
        seriqc_lib,
        bms_january_1min_boundaries,
        Kt=0.9,
        Kn=Kn_max,
    )


def test_SQC_2C_component_test_correct_max_Kt(
    seriqc_lib, bms_january_1min_boundaries
):
    """Test that flag is correctly set to 2, for a point on the boundary"""

    *__, Kt_max, __, __ = bms_january_1min_boundaries

    assert_python_matches_c_SQC_2C(
        seriqc_lib,
        bms_january_1min_boundaries,
        Kt=Kt_max,
        Kn=0.8,
    )


def test_SQC_2C_component_test_correct_max_Kt_Kn(
    seriqc_lib, bms_january_1min_boundaries
):
    """Test that flag is correctly set to 2, for a point on the boundary"""

    *__, Kt_max, Kn_max, __ = bms_january_1min_boundaries

    assert_python_matches_c_SQC_2C(
        seriqc_lib,
        bms_january_1min_boundaries,
        Kt=Kt_max,
        Kn=Kn_max,
    )


def test_SQC_2C_component_greater_than_Kn_low_error(
    seriqc_lib,
    bms_january_1min_boundaries,
):
    """Test when Kn>Kt but within Gompertz top boundary.

    Top_L=85.9 and Top_R=96
    """

    *__, Kn_max, __ = bms_january_1min_boundaries

    assert_python_matches_c_SQC_2C(
        seriqc_lib,
        bms_january_1min_boundaries,
        Kt=0.9,
        Kn=Kn_max + 0.04,
    )


def test_SQC_2C_component_greater_than_Kn_high_Kt_high(
    seriqc_lib,
    bms_january_1min_boundaries,
):
    """Test Kn > Kn_max & Kt > Top_R"""

    *__, Kn_max, __ = bms_january_1min_boundaries

    assert_python_matches_c_SQC_2C(
        seriqc_lib,
        bms_january_1min_boundaries,
        Kt=0.97,
        Kn=Kn_max + 0.05,
    )


def test_SQC_2C_component_Kn_below_zero_part_1(
    seriqc_lib, bms_january_1min_boundaries
):
    """Test when (Kn < 0) & (Kt <= Bot_R) & (Kt >= Bot_L)"""

    assert_python_matches_c_SQC_2C(
        seriqc_lib,
        bms_january_1min_boundaries,
        Kt=0.4,
        Kn=-0.04,
    )


def test_SQC_2C_component_Kn_below_zero_part_2(
    seriqc_lib, bms_january_1min_boundaries
):
    """Test when (Kn < 0) & (Kt < Bot_L)"""

    assert_python_matches_c_SQC_2C(
        seriqc_lib,
        bms_january_1min_boundaries,
        Kt=-0.01,
        Kn=-0.04,
    )


def test_SQC_2C_component_greater_than_Kn_high_error(
    seriqc_lib, bms_january_1min_boundaries
):
    """Similar to test_two_component_greater_than_Kn_low_error; higher error"""

    *__, Kn_max, __ = bms_january_1min_boundaries

    assert_python_matches_c_SQC_2C(
        seriqc_lib,
        bms_january_1min_boundaries,
        Kt=0.9,
        Kn=Kn_max + 0.08,
    )


def test_SQC_2C_component_greater_than_Kn_very_high_error(
    seriqc_lib, bms_january_1min_boundaries
):
    """Similar to test_two_component_greater_than_Kn_very_high_error

    This test has errors higher than 23%, hence the flags are 92-93
    as errors that are greater than 23%, gets resolved to 23%.
    """

    *__, Kn_max, __ = bms_january_1min_boundaries

    assert_python_matches_c_SQC_2C(
        seriqc_lib,
        bms_january_1min_boundaries,
        Kt=0.9,
        Kn=Kn_max + 0.25,
    )


def test_SQC_2C_greater_than_Kt_low_error(
    seriqc_lib, bms_january_1min_boundaries
):
    """Test flagging of a point to the immediate right of Kt_max"""

    *__, Kt_max, __, __ = bms_january_1min_boundaries

    assert_python_matches_c_SQC_2C(
        seriqc_lib,
        bms_january_1min_boundaries,
        Kt=Kt_max + 0.09,
        Kn=0.2,
    )


def test_SQC_2C_point_right_of_gompertz(
    seriqc_lib, bms_january_1min_boundaries
):
    """Test low Kn and to the right of Gompertz curve with Kt < Kt_max"""

    assert_python_matches_c_SQC_2C(
        seriqc_lib,
        bms_january_1min_boundaries,
        Kt=0.85,
        Kn=0.1,
    )


def test_SQC_2C_point_below_kn_max(seriqc_lib, bms_january_1min_boundaries):
    """Test point below Kn_max and directly to the right of Kt_max"""

    assert_python_matches_c_SQC_2C(
        seriqc_lib,
        bms_january_1min_boundaries,
        Kt=0.97,
        Kn=0.72,
    )


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
