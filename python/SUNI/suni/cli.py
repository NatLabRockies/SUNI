# -*- coding: utf-8 -*-
"""SUNI CLI"""
import os
import logging
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

import click
from tqdm import tqdm
import pandas as pd

from suni.framework import Uprocess, uDat
from suni.instrument_uncertainty import extract_rad_uncertainty
from suni.utilities import (
    extract_time_from_input_data,
    extract_irradiance_from_input_data,
)
from suni.utilities.reports import (
    compile_popup_report,
    compile_standard_report,
)
from suni.utilities.configs import data_from_ini, data_from_json


logger = logging.getLogger(__name__)


MIN_RECORDS_PER_PROCESS = 5
CHUNK_SIZE = 50


class SUNIInputDataError(ValueError):
    """SUNI input data error"""


@click.command(no_args_is_help=True)
@click.argument("config", type=click.Path(exists=True))
@click.option(
    "--max_workers",
    "-mw",
    type=int,
    default=None,
    help="Number of processes to use. Default uses all available CPU cores",
)
def main(config, max_workers):
    handler = logging.StreamHandler()
    handler.setLevel("INFO")
    logger.addHandler(handler)
    logger.setLevel("INFO")

    if Path(config).suffix.casefold() == ".ini":
        cfg = data_from_ini(config)
    else:
        cfg = data_from_json(config)
    cfg["max_workers"] = max_workers
    return process_from_config(cfg, from_gui=False)


def process_from_config(cfg, from_gui=True):
    if not from_gui:
        return _process(cfg, from_gui=from_gui)

    try:
        return _process(cfg, from_gui=from_gui)
    except KeyboardInterrupt as cancel:
        raise cancel
    except Exception as err:
        msg = f"{type(err).__name__}:\n{err}"
        return msg


def _read_data(input_file):
    try:
        input_data = pd.read_csv(
            input_file,
            header=0,
            names=["DATE", "MST", "GHI", "DNI", "DHI"],
            index_col=False,
        )
    except pd.errors.ParserError:
        msg = (
            "Found incorrect number of columns in input data! Ensure your "
            "input data starts with at least the following columns: "
            '["DATE", "TIME", "GHI", "DNI", "DHI"]'
        )
        logger.error(msg)
        raise SUNIInputDataError(msg) from None
    return input_data


def _process(cfg, from_gui=True):
    proc_start_time = datetime.now()
    max_workers = cfg.get("max_workers")
    input_file = Path(cfg["InputFile"])
    of = cfg.get("OutputFile", f"{input_file.stem}_Unc.csv")
    if not of.endswith(".csv"):
        of = f"{of}.csv"
    of = Path(of)
    input_data = _read_data(input_file)

    max_workers = os.cpu_count() if max_workers is None else max_workers
    logger.info(
        "Running SUNI for %d records using %d process(es)",
        len(input_data),
        max_workers,
    )
    if max_workers > 1:
        results = run_mp(
            input_file, input_data, cfg, max_workers, from_gui=from_gui
        )
    else:
        results = run_sp(input_file, input_data, cfg, from_gui=from_gui)

    results = pd.concat([input_data, results], axis=1).round(decimals=1)

    standard_report = compile_standard_report(results, cfg, proc_start_time)
    popup_report = compile_popup_report(results, cfg)

    results = _finalize_format(results, cfg)
    results.to_csv(of, index=False) # , float_format="%.1f")
    logger.info("Results written to %s", str(of))

    rf = of.parent / f"{of.stem}_report.txt"
    with open(rf, "w") as fh:
        fh.write(standard_report)
    logger.info("\n---")
    logger.info(standard_report)
    logger.info("---\n")
    logger.info("Report written to %s", str(rf))

    return_dict = {"out_file": str(of), "report": popup_report}
    return return_dict


def _finalize_format(results, cfg):
    if int(cfg.get("DateFormat", 0)):
        date_col = "Date (YYYY-MM-DD)"
    else:
        date_col = "Date (MM/DD/YYYY)"

    int_cols = ["qcGHI", "qcDNI", "qcDHI", "uCode", "SQCcode"]
    results[int_cols] = results[int_cols].astype(int)
    for col in ["qcGHI", "qcDNI", "qcDHI"]:
        results[col] = results[col].map(lambda x: f"{x:02d}")

    rename_mapping = {
        "DATE": date_col,
        "MST": "Time (HH:MM)",
        "GHI": "GHI (W/m^2)",
        "qcGHI": "GHI SERI QC Flag",
        "U95GHI": "GHI Uncertainty (+/-%)",
        "uCode": "GHI Uncertainty Code",
        "DNI": "DNI (W/m^2)",
        "qcDNI": "DNI SERI QC Flag",
        "U95DNI": "DNI Uncertainty (+/-%)",
        "DHI": "DHI (W/m^2)",
        "qcDHI": "DHI SERI QC Flag",
        "U95DHI": "DHI Uncertainty (+/-%)",
        "UoSys": "System Uncertainty (+/-%)",
        "Ufield": "Field Uncertainty (+/-%)",
        "Urads": "Urads (+/-%)",
    }

    results = results.rename(columns=rename_mapping)
    results["DNI Uncertainty Code"] = results["GHI Uncertainty Code"]
    results["DHI Uncertainty Code"] = results["GHI Uncertainty Code"]
    col_order = [
        date_col,
        "Time (HH:MM)",
        "GHI (W/m^2)",
        "GHI SERI QC Flag",
        "GHI Uncertainty (+/-%)",
        "GHI Uncertainty Code",
        "DNI (W/m^2)",
        "DNI SERI QC Flag",
        "DNI Uncertainty (+/-%)",
        "DNI Uncertainty Code",
        "DHI (W/m^2)",
        "DHI SERI QC Flag",
        "DHI Uncertainty (+/-%)",
        "DHI Uncertainty Code",
    ]
    if int(cfg.get("ExtendedRpt", 0)):
        col_order += [
            "System Uncertainty (+/-%)",
            "Field Uncertainty (+/-%)",
            "Urads (+/-%)",
        ]

    return results[col_order].fillna("-9900")


def _row_to_data(row, cfg, ghi_rad_u, dni_rad_u, dhi_rad_u):
    d_fmt = int(cfg.get("DateFormat", 0))
    year, month, day, hour, minute = extract_time_from_input_data(row, d_fmt)
    ghi, dni, dhi = extract_irradiance_from_input_data(row)
    return uDat(
        cfg["StationID"],
        cfg["SERIQCpath"],
        year,
        month,
        day,
        hour,
        minute,
        int(cfg["Interval"]),
        ghi,
        dni,
        dhi,
        ghi_rad_u,
        dni_rad_u,
        dhi_rad_u,
        float(cfg["MinDNI"]),
        float(cfg["MaxZEN"]),
        int(cfg["MaxQC"]),
        int(cfg["MaxSysUncert"]),
    )


def run_mp(input_file, input_data, cfg, max_workers, from_gui):
    results = {}
    ghi_rad_u, dni_rad_u, dhi_rad_u = extract_rad_uncertainty(cfg)
    chunk_size = max(CHUNK_SIZE, MIN_RECORDS_PER_PROCESS * max_workers)

    progress_count = 0
    with ProcessPoolExecutor(max_workers=max_workers) as executor:

        for out in _iter_mp_chunks(
            input_file, input_data, from_gui, chunk_size=chunk_size
        ):
            chunk, pbar = (out, None) if from_gui else out
            futures = _submit_for_processing(
                executor, chunk, cfg, ghi_rad_u, dni_rad_u, dhi_rad_u
            )

            for future in as_completed(futures):
                row_ind = futures.pop(future)
                try:
                    data = future.result()
                except KeyboardInterrupt as cancel:
                    raise cancel
                except Exception as err:
                    msg = (
                        f"Error processing input data on line {row_ind + 2}:"
                        f"\n{err}"
                    )
                    raise type(err)(msg)

                results[row_ind] = data.as_result_dict()
                progress_count += 1
                if from_gui:
                    print(int(progress_count / len(input_data) * 100))
                else:
                    pbar.update(1)

    results = pd.DataFrame(results).T.sort_index()
    return results


def run_sp(input_file, input_data, cfg, from_gui):
    results = {}
    ghi_rad_u, dni_rad_u, dhi_rad_u = extract_rad_uncertainty(cfg)
    nun_to_run = len(input_data)
    for ind, row_ind, row in _iter_df(input_file, input_data, from_gui):
        data = _row_to_data(row, cfg, ghi_rad_u, dni_rad_u, dhi_rad_u)

        try:
            data = Uprocess(data, pressure=820, temp=11)
        except KeyboardInterrupt as cancel:
            raise cancel
        except Exception as err:
            msg = (
                f"Error processing input data on line {row_ind + 2}:"
                f"\n{err}"
            )
            raise type(err)(msg)

        results[row_ind] = data.as_result_dict()
        if from_gui:
            print(int(ind / nun_to_run * 100))

    results = pd.DataFrame(results).T.sort_index()
    return results


def _iter_df(input_file, input_data, from_gui):
    if from_gui:
        yield from _iter_enumerated_df(input_data)

    else:
        for out in tqdm(
            _iter_enumerated_df(input_data),
            total=len(input_data),
            desc=input_file.stem,
        ):
            yield out


def _iter_enumerated_df(input_data):
    for ind, (row_ind, row) in enumerate(input_data.iterrows(), start=1):
        yield ind, row_ind, row


def _iter_mp_chunks(input_file, data, from_gui, chunk_size):
    if from_gui:
        yield from _chunked_data(data, chunk_size=chunk_size)

    else:
        with tqdm(total=len(data), desc=input_file.stem) as pbar:
            for chunk in _chunked_data(data, chunk_size=chunk_size):
                yield chunk, pbar


def _chunked_data(data, chunk_size):
    for start in range(0, len(data), chunk_size):
        yield data[start : start + chunk_size]


def _submit_for_processing(
    executor, data_chunk, cfg, ghi_rad_u, dni_rad_u, dhi_rad_u
):
    future_to_row = {}
    for row_ind, row in data_chunk.iterrows():
        data = _row_to_data(row, cfg, ghi_rad_u, dni_rad_u, dhi_rad_u)
        future = executor.submit(Uprocess, data, pressure=820, temp=11)
        future_to_row[future] = row_ind
    return future_to_row


# python -c "import json; from suni.cli import process_from_config; fh = open('sample_config.json'); cfg = json.load(fh); fh.close(); process_from_config(cfg)"
