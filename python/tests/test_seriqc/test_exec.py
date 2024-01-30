"""Test SERIQC exec functions."""
from pathlib import Path

import pytest
import numpy as np

from seriqc.exec import seriqc_from_file


@pytest.mark.parametrize(
    "test_case",
    [
        (1, 1, 1, 1, 1, 8, 8, 99, 0),
        (0, 1, 1, 1, 1, 0, 0, 0, 2),
        (1, 1, 1, 1, 1, 8, 8, 99, 0),
        (12, 1, 1, 1, 1, 8, 8, 99, 0),
        (13, 1, 1, 1, 1, 0, 0, 0, 2),
        (1, 0, 1, 1, 1, 0, 0, 0, 4),
        (1, 1, 1, 1, 1, 8, 8, 99, 0),
        (1, 31, 1, 1, 1, 8, 8, 99, 0),
        (1, 32, 1, 1, 1, 0, 0, 0, 4),
        (1, 1, 0, 1, 1, 8, 8, 99, 0),
        (1, 1, 24, 0, 1, 8, 8, 99, 0),
        (1, 1, 25, 0, 1, 0, 0, 0, 40),
        (1, 1, 1, -1, 1, 0, 0, 0, 16),
        (1, 1, 1, 0, 1, 8, 8, 99, 0),
        (1, 1, 1, 59, 1, 8, 8, 99, 0),
        (1, 1, 1, 60, 1, 0, 0, 0, 16),
        (1, 1, 0, -1, 1, 0, 0, 0, 48),
        (1, 1, 0, 0, 1, 8, 8, 99, 0),
        (1, 1, 24, 0, 1, 8, 8, 99, 0),
        (1, 1, 24, 1, 1, 0, 0, 0, 32),
        (1, 1, 1, 1, 0, 0, 0, 0, 64),
        (1, 1, 1, 1, 1, 8, 8, 99, 0),
        (1, 1, 1, 1, 60, 8, 8, 99, 0),
        (1, 1, 1, 1, 61, 0, 0, 0, 64),
        (0, 0, -1, -1, 0, 0, 0, 0, 126),
        (1, 0, -1, -1, 0, 0, 0, 0, 124),
        (1, 1, -1, -1, 0, 0, 0, 0, 120),
        (0, 1, -1, -1, 0, 0, 0, 0, 122),
        (0, 0, 1, 1, 1, 0, 0, 0, 6),
    ],
)
def test_seriqc_from_file_time_validation(qc0_info, test_case):
    """Test time validation of python to C code"""

    site, qc0_dir = qc0_info
    ghi = 4500
    dni = 4500
    dhi = 9000

    month, day, hour, minute, interval, *expected_output = test_case

    ghi_flag, dni_flag, dhi_flag, *__, return_code = seriqc_from_file(
        site,
        qc0_dir,
        2000,
        month,
        day,
        hour,
        minute,
        interval,
        ghi,
        dni,
        dhi,
    )
    assert [ghi_flag, dni_flag, dhi_flag, return_code] == expected_output


def test_seriqc_from_file_bad_input(qc0_info, tmp_path):
    """Test bad file input to function."""

    site, qc0_dir = qc0_info
    bad_qc0_fp = tmp_path / f"s_{site}.qc0"
    bad_qc0_dir = str(tmp_path)

    ghi = 4500
    dni = 4500
    dhi = 9000

    ghi_flag, dni_flag, dhi_flag, *__, return_code = seriqc_from_file(
        "      ",
        qc0_dir,
        2000,
        1,
        1,
        1,
        1,
        1,
        ghi,
        dni,
        dhi,
    )
    assert (ghi_flag, dni_flag, dhi_flag, return_code) == (0, 0, 0, 1)

    ghi_flag, dni_flag, dhi_flag, *__, return_code = seriqc_from_file(
        site,
        bad_qc0_dir,
        2000,
        1,
        1,
        1,
        1,
        1,
        ghi,
        dni,
        dhi,
    )
    assert (ghi_flag, dni_flag, dhi_flag, return_code) == (0, 0, 0, 128)

    with open(Path(qc0_dir) / f"s_{site}.qc0", "r") as fh:
        lines = fh.readlines()

    lines[9] = lines[9].replace("JAN", "DNE")
    with open(bad_qc0_fp, "w") as fh:
        fh.writelines(lines)

    ghi_flag, dni_flag, dhi_flag, *__, return_code = seriqc_from_file(
        site,
        bad_qc0_dir,
        2000,
        1,
        1,
        1,
        1,
        1,
        ghi,
        dni,
        dhi,
    )
    assert (ghi_flag, dni_flag, dhi_flag, return_code) == (0, 0, 0, 256)


def test_bad_kt_kn_input(qc0_info, tmp_path):
    """Test bad Kt/Kn input"""

    site, qc0_dir = qc0_info
    bad_qc0_fp = tmp_path / f"s_{site}.qc0"
    bad_qc0_dir = str(tmp_path)
    ghi = 4500
    dni = 4500
    dhi = 9000

    with open(Path(qc0_dir) / f"s_{site}.qc0", "r") as fh:
        lines = fh.readlines()

    lines[13] = lines[13].replace("83-95/95/00/00;", "00-00/00/00/00")
    with open(bad_qc0_fp, "w") as fh:
        fh.writelines(lines)

    ghi_flag, dni_flag, dhi_flag, *__, return_code = seriqc_from_file(
        site,
        bad_qc0_dir,
        2000,
        5,
        1,
        12,
        1,
        1,
        ghi,
        dni,
        dhi,
    )
    assert (ghi_flag, dni_flag, dhi_flag, return_code) == (0, 0, 0, 6144)


def test_bad_curve_input(qc0_info, tmp_path):
    """Test bad curve input"""

    site, qc0_dir = qc0_info
    bad_qc0_fp = tmp_path / f"s_{site}.qc0"
    bad_qc0_dir = str(tmp_path)
    ghi = 4500
    dni = 4500
    dhi = 9000

    with open(Path(qc0_dir) / f"s_{site}.qc0", "r") as fh:
        lines = fh.readlines()

    lines[12] = lines[12].replace("4-10 1-15/15/00/00", "0-00 0-00/00/00/00")
    with open(bad_qc0_fp, "w") as fh:
        fh.writelines(lines)

    ghi_flag, dni_flag, dhi_flag, *__, return_code = seriqc_from_file(
        site,
        bad_qc0_dir,
        2000,
        4,
        1,
        12,
        1,
        1,
        ghi,
        dni,
        dhi,
    )
    assert (ghi_flag, dni_flag, dhi_flag, return_code) == (0, 0, 0, 1536)


@pytest.mark.parametrize(
    "test_case",
    [
        (1, -20, -20, -20, 7, 7, 7),
        (0, 100, 100, 100, 8, 8, 8),
        (12, 200, 400, 94, 46, 47, 47),
        (12, 160, 400, 95, 70, 71, 71),
        (12, 100, 400, 96, 95, 95, 1),
        (12, 80, 400, 97, 96, 96, 1),
        (12, 417, 105, 417 - 100 * np.cos(np.deg2rad(62.85)), 9, 9, 9),
        (12, 400, 500, 400 - 500 * np.cos(np.deg2rad(62.85)), 3, 3, 3),
        (12, 9000, 100, 400 - 100 * np.cos(np.deg2rad(62.85)), 99, 16, 16),
        (12, 400, 9000, 400 - 500 * np.cos(np.deg2rad(62.85)), 2, 99, 2),
        (12, 200, 400, 9000, 44, 45, 99),
        (12, 160, 400, 9000, 64, 65, 99),
        (12, 100, 400, 9000, 95, 95, 99),
        (12, 80, 400, 9000, 96, 96, 99),
        (12, 9, 9000, 9000, 7, 99, 99),
        (12, 1, 9000, 1, 7, 99, 7),
        (12, 4500, 4500, 4500, 8, 8, 8),
        (12, 9000, 4500, 4500, 99, 8, 8),
        (12, 4500, 9000, 4500, 8, 99, 8),
        (12, 4500, 4500, 9000, 8, 8, 99),
        (12, 9000, 9000, 9000, 99, 99, 99),
        (7, 1, 9000, 1, 1, 99, 8),
        (7, 9, 9000, 9000, 1, 99, 99),
        (12, 9000, 1020, 140, 99, 2, 2),
        (12, 4.723, 9000, 9000, 7, 99, 99),
        (12, 9000, -11, 9000, 99, 7, 99),
        (12, 9000, -11, -1.166, 99, 7, 7),
        (12, 133, 413, 9000, 94, 94, 99),
        (12, 106, 413, 9000, 95, 95, 99),
        (12, 66, 413, 9000, 96, 96, 99),
        (12, 53, 413, 9000, 97, 97, 99),
        (8, 0.1, 9000, 0.1, 1, 99, 1),
        (7, 0.0083978, 9000, 9000, 1, 99, 99),
    ],
)
def test_nominal_exec(qc0_info, test_case):
    """Test a nominal run (truth values computed using C code)"""

    site, qc0_dir = qc0_info
    month, interval = 1, 60
    hour, ghi, dni, dhi, *truth_flags = test_case
    if hour:
        minute = 30
        day = 1
    else:
        minute = 30
        day = 2

    ghi_flag, dni_flag, dhi_flag, *__, return_code = seriqc_from_file(
        site,
        qc0_dir,
        2000,
        month,
        day,
        hour,
        minute,
        interval,
        ghi,
        dni,
        dhi,
    )

    assert return_code == 0
    assert [ghi_flag, dni_flag, dhi_flag] == truth_flags


@pytest.mark.parametrize(
    "test_case",
    [
        (1, 7, 25, 3.4753, 0.225650, 4.10509, 1, 1, 8),
        (1, 7, 26, 3.9072, 0.251888, 4.50005, 1, 1, 1),
        (1, 8, 32, 105.179, 0.377831, 105.89, 3, 3, 3),
        (1, 11, 24, 338.072, 126.07, 265.142, 11, 10, 10),
        (3, 15, 5, 18.083, 0.215152, 18.5682, 7, 2, 2),
        (10, 9, 9, 213.496, 277.277, 156.698, 18, 19, 19),
        (10, 9, 12, 244.159, 298.688, 149.258, 11, 10, 10),
        (10, 9, 14, 236.727, 231.391, 152.035, 19, 18, 18),
        (10, 9, 16, 237.137, 173.43, 149.798, 35, 34, 34),
        (10, 9, 45, 270.915, 309.846, 183.669, 10, 11, 11),
        (24, 12, 31, 804.681, 884.924, 346.868, 8, 56, 56),
        (25, 13, 54, 465.163, 548.49, 227.984, 3, 3, 3),
    ],
)
def test_nominal_nrelsr_site(test_data_dir, test_case):
    """Spot test nominal run cases"""

    month = interval = 1
    site = "NRELSR"

    day, hour, minute, ghi, dni, dhi, *truth_flags = test_case

    ghi_flag, dni_flag, dhi_flag, *__, return_code = seriqc_from_file(
        site,
        test_data_dir,
        2021,
        month,
        day,
        hour,
        minute,
        interval,
        ghi,
        dni,
        dhi,
    )

    assert return_code == 0
    assert [ghi_flag, dni_flag, dhi_flag] == truth_flags


@pytest.mark.parametrize(
    "test_case",
    [
        (1, 7, 25, 3.4753, 0.225650, 4.10509, 1, 1, 8),
        (1, 7, 26, 3.9072, 0.251888, 4.50005, 1, 1, 1),
    ],
)
def test_nominal_benchmarking_exec(qc0_info, test_case):
    """Test a nominal run with benchmarking data"""

    __, qc0_dir = qc0_info
    month = interval = 1
    day, hour, minute, ghi, dni, dhi, *truth_flags = test_case
    ghi_flag, dni_flag, dhi_flag, *__, return_code = seriqc_from_file(
        "NRELSR",
        qc0_dir,
        2021,
        month,
        day,
        hour,
        minute,
        interval,
        ghi,
        dni,
        dhi,
    )

    assert return_code == 0
    assert [ghi_flag, dni_flag, dhi_flag] == truth_flags


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
