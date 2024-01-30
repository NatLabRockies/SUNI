"""Test against benchmark C data."""
import pytest
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd

import seriqc
from seriqc.exec import seriqc_from_file
from seriqc.utilities import ErrorCode


SERIQC_DIR = Path(__file__).parent.parent.parent
BIT_SHIFTS = np.arange(len(ErrorCode))
pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def save_benchmarking_data(pytestconfig):
    """Check wether user has requested save of the benchmarking results"""
    return pytestconfig.getoption("save")


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


def _extract_date(row):
    """Extract and split date from CSV row input."""
    return tuple(int(d) for d in row["DATE"].split("/"))


def _extract_time(row):
    """Extract and split time from CSV row input."""
    return tuple(int(d) for d in row["MST"].split(":"))


def _compute_ret_value_counts(ret_values):
    """Compute return value counts given a set of return values."""
    sums = ((ret_values.reshape(-1, 1) & (1 << BIT_SHIFTS)) > 0).sum(axis=0)
    good_codes = (ret_values == 0).sum()
    return [good_codes] + list(sums)


def _compute_return_counts(data):
    """Compute return value counts for output data."""
    sums = _compute_ret_value_counts(data["P_RET"].values)
    return pd.DataFrame(
        {"Error": ["Good"] + list(BIT_SHIFTS), "P_Count": sums}
    )


def _parse_c_code_count_output(fp):
    """Parse in C code baseline counts"""
    df = pd.read_csv(fp)
    flag_counts = df.iloc[:100]
    return_counts = pd.DataFrame(
        df.iloc[100:].values[1:, :2], columns=df.iloc[100:].values[0, :2]
    )
    return flag_counts, return_counts


@pytest.mark.parametrize(
    "input_data_fn, site, interval",
    [
        ("SRRL1987_05.csv", "NRELSR", 5),
        ("SRRL1987_15.csv", "NRELSR", 15),
        ("SRRL1987_30.csv", "NRELSR", 30),
        ("SRRL1987_60.csv", "NRELSR", 60),
        ("SRRL2004_01.csv", "NRELSR", 1),
        ("SRRL2007_01.csv", "NRELSR", 1),
        ("SRRL2007_30.csv", "NRELSR", 30),
        ("SRRL2007_60.csv", "NRELSR", 60),
        ("SRRL2007_TIME_01.csv", "NRELSR", 1),
        ("SRRL2007_SITE_01.csv", "XXXX", 1),
        ("SRRL2007_BOUNDARY1_01.csv", "BOUNDARY1", 1),
        ("SRRL2007_CLOCK_01.csv", "CLOCK", 1),
        ("SRRL2007_INTERVAL_01.csv", "NRELSR", 61),
        ("SRRL2007_INCREMENTAL.csv", "NRELSR", 1),
        ("SRRL2007_TIMERAMP.csv", "NRELSR", 1),
        ("SRRL2007_FORMAT_01.csv", "BADFORMAT", 1),
    ],
)
def test_nominal_benchmarking_exec(
    test_data_dir,
    input_data_fn,
    site,
    interval,
    save_benchmarking_data,
):
    """Test a nominal run against benchmark C data"""

    input_data = pd.read_csv(
        test_data_dir / input_data_fn,
        header=0,
        names=[
            "DATE",
            "MST",
            "GHI",
            "DNI",
            "DHI",
            "C_GHI_FLG",
            "C_DNI_FLG",
            "C_DHI_FLG",
        ],
    )
    input_data[["Month", "Day", "Year"]] = input_data.apply(
        _extract_date, axis="columns", result_type="expand"
    )

    input_data[["Hour", "Minute"]] = input_data.apply(
        _extract_time, axis="columns", result_type="expand"
    )

    data_cols = ["GHI", "DNI", "DHI"]

    future_to_row = {}
    results = {}
    with ProcessPoolExecutor() as executor:
        for row_ind, row in input_data.iterrows():
            ghi, dni, dhi = row[data_cols].astype(float)
            if ghi < -9900:
                ghi *= -1
            if dni < -9900:
                dni *= -1
            if dhi < -9900:
                dhi *= -1
            future = executor.submit(
                seriqc_from_file,
                site=site,
                qc0_dir=test_data_dir,
                year=int(row["Year"]),
                month=int(row["Month"]),
                day=int(row["Day"]),
                hour=int(row["Hour"]),
                minute=int(row["Minute"]),
                interval=int(interval),
                ghi=ghi,
                dni=dni,
                dhi=dhi,
                pressure=820,
                temp=11,
            )
            future_to_row[future] = row_ind

        for future in as_completed(future_to_row):
            row_ind = future_to_row.pop(future)
            ghi_flag, dni_flag, dhi_flag, *__, return_code = future.result()
            results[row_ind] = {
                "P_GHI_FLG": ghi_flag,
                "P_DNI_FLG": dni_flag,
                "P_DHI_FLG": dhi_flag,
                "P_RET": return_code,
            }

    results = pd.DataFrame(results).T.sort_index()

    flag_counts, return_counts = _parse_c_code_count_output(
        test_data_dir / "c_code_outputs" / f"FlagCount_{input_data_fn}"
    )
    python_return_counts = _compute_return_counts(results)

    assert np.allclose(
        return_counts["Count"].values.astype(int),
        python_return_counts["P_Count"].values.astype(int),
    )

    records_mismatch = (
        (input_data["C_GHI_FLG"] != results["P_GHI_FLG"])
        | (input_data["C_DNI_FLG"] != results["P_DNI_FLG"])
        | (input_data["C_DHI_FLG"] != results["P_DHI_FLG"])
    )
    num_records_mismatch = records_mismatch.sum()

    frac_mismatch = num_records_mismatch / input_data.shape[0]
    tolerance = 1 / 500_000
    assert frac_mismatch < tolerance, f"{frac_mismatch:.2%}"

    if save_benchmarking_data:
        comparison_string = (
            f"{num_records_mismatch:,d}/{input_data.shape[0]:,d} "
            f"({frac_mismatch:.2%})"
        )

        python_return_counts = pd.concat(
            [
                python_return_counts,
                pd.DataFrame(
                    {
                        "Error": ["Number of records with mismatching flags:"],
                        "P_Count": [comparison_string],
                    }
                ),
            ]
        ).reset_index(drop=True)

        python_flag_counts = _compute_counts(results)[
            ["P_GHI", "P_DNI", "P_DHI"]
        ]
        counts = pd.concat([flag_counts, python_flag_counts], axis=1)
        counts = pd.concat(
            [counts, return_counts, python_return_counts], axis=1
        )
        out_fn = f"{Path(input_data_fn).stem}_python_flag_counts.csv"
        counts.to_csv(
            test_data_dir / "python_code_outputs" / out_fn, index=False
        )

        out_cols = [
            "DATE",
            "MST",
            "GHI",
            "DNI",
            "DHI",
            "C_GHI_FLG",
            "C_DNI_FLG",
            "C_DHI_FLG",
            "P_GHI_FLG",
            "P_DNI_FLG",
            "P_DHI_FLG",
            "P_RET",
            "MISMATCH",
        ]
        input_data["P_GHI_FLG"] = results["P_GHI_FLG"].values
        input_data["P_DNI_FLG"] = results["P_DNI_FLG"].values
        input_data["P_DHI_FLG"] = results["P_DHI_FLG"].values
        input_data["P_RET"] = results["P_RET"].values
        input_data["MISMATCH"] = None
        input_data.loc[records_mismatch, "MISMATCH"] = "*"
        out_fn = f"{Path(input_data_fn).stem}_with_python_flags.csv"
        input_data[out_cols].to_csv(
            test_data_dir / "python_code_outputs" / out_fn, index=False
        )
        if "SRRL2007_01" in input_data_fn:
            june_data = input_data[
                (input_data["Month"] == 6) & (input_data["Day"] == 21)
            ].copy()

            output = []
            for row_ind, row in june_data.iterrows():
                ghi, dni, dhi = row[data_cols].astype(float)

                *__, etr, __, sol_zen, __ = seriqc_from_file(
                    site="NRELSR",
                    qc0_dir=test_data_dir,
                    year=int(row["Year"]),
                    month=int(row["Month"]),
                    day=int(row["Day"]),
                    hour=int(row["Hour"]),
                    minute=int(row["Minute"]),
                    interval=1,
                    ghi=ghi,
                    dni=dni,
                    dhi=dhi,
                )
                output.append((sol_zen, etr))

            out_data = pd.DataFrame(output, columns=["Solzen", "ETR"])
            out_data["Date"] = june_data["DATE"].values
            out_data["Time"] = june_data["MST"].values

            out_data[["Date", "Time", "Solzen", "ETR"]].to_csv(
                test_data_dir
                / "python_code_outputs"
                / "SRRL_2007_June_21_solzen_ETR_data.csv",
                index=False,
            )


def _compute_counts(results):
    """Compute flag counts."""
    ghi_counts = (
        results["P_GHI_FLG"]
        .value_counts()
        .rename_axis("Flag")
        .reset_index(name="P_GHI")
    )
    dni_counts = (
        results["P_DNI_FLG"]
        .value_counts()
        .rename_axis("Flag")
        .reset_index(name="P_DNI")
    )
    dhi_counts = (
        results["P_DHI_FLG"]
        .value_counts()
        .rename_axis("Flag")
        .reset_index(name="P_DHI")
    )
    counts = pd.DataFrame(data=range(100), columns=["Flag"])
    counts = counts.merge(ghi_counts, how="left", on="Flag")
    counts = counts.merge(dni_counts, how="left", on="Flag")
    counts = counts.merge(dhi_counts, how="left", on="Flag")
    counts = counts.fillna(0).astype(int)
    return counts


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
