import os
import json
import configparser
from math import sqrt
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

import click

from tqdm import tqdm
import pandas as pd

from suni.framework import Uprocess, uDat, ErrorCode
from suni.instrument_uncertainty import extract_rad_uncertainty
from suni.utilities import (
    format_date,
    convert_to_year_first,
    compute_parameter_stats,
    extract_time_from_input_data,
    extract_irradiance_from_input_data,
)
from suni.utilities.reports import (
    compile_popup_report,
    compile_standard_report,
)

CONFIG_KEYS = [
    "StationID",
    "InputFile",
    "OutputFile",
    "SERIQCpath",
    "Interval",
    "GHIid",
    "GHImodel",
    "GHIclass",
    "GHIclassUncert",
    "GHIcalUncert",
    "GHIcalDate",
    "GHIdueDate",
    "GHIradUncert",
    "DNIid",
    "DNImodel",
    "DNIclass",
    "DNIclassUncert",
    "DNIcalUncert",
    "DNIcalDate",
    "DNIdueDate",
    "DNIradUncert",
    "DHIid",
    "DHImodel",
    "DHIclass",
    "DHIclassUncert",
    "DHIcalUncert",
    "DHIcalDate",
    "DHIdueDate",
    "DHIradUncert",
    "MaxSysUncert",
    "MaxQC",
    "MinDNI",
    "MaxZEN",
    "DateFormat",
    "ExtendedRpt",
]


def _data_from_ini(fp):
    cfg = configparser.ConfigParser()
    cfg.read(fp)
    config = dict(cfg.items("SUNI"))

    return {
        key: config[key.lower()]
        for key in CONFIG_KEYS
        if key.lower() in config
    }


def _data_from_json(fp):
    with open(fp, "r") as fh:
        data = json.load(fh)
    return data


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
    if Path(config).suffix.casefold() == ".ini":
        cfg = _data_from_ini(config)
    else:
        cfg = _data_from_json(config)
    # cfg = _format_config_data(cfg)
    cfg["max_workers"] = max_workers
    return process_from_config(cfg, from_gui=False)


def process_from_config(cfg, from_gui=True):
    proc_start_time = datetime.now()
    max_workers = cfg.get("max_workers")
    input_file = Path(cfg["InputFile"])
    of = cfg.get("OutputFile", f"{input_file.stem}_Unc.csv")
    input_data = pd.read_csv(
        input_file,
        header=0,
        names=["DATE", "MST", "GHI", "DNI", "DHI"],
    )

    max_workers = os.cpu_count() if max_workers is None else max_workers
    # print(
    #     f"Kicking off SUNI for {len(input_data):,d} records "
    #     f"using {max_workers:d} process(es)"
    # )
    if max_workers > 1:
        results = run_mp(input_data, cfg, max_workers, from_gui=from_gui)
    else:
        results = run_sp(input_data, cfg, from_gui=from_gui)

    int_cols = ["qcGHI", "qcDNI", "qcDHI", "uCode", "SQCcode"]
    results[int_cols] = results[int_cols].astype(int)
    results = pd.concat([input_data, results], axis=1)

    standard_report = compile_standard_report(results, cfg, proc_start_time)
    popup_report = compile_popup_report(results, cfg)

    results = _finalize_format(results, cfg)
    results.to_csv(of, index=False, float_format="%.1f")
    # print(f"Results written to {str(of)}")

    rf = Path(of).parent / f"{input_file.stem}_Report.txt"
    with open(rf, "w") as fh:
        fh.write(standard_report)
    # print(standard_report)
    # print(f"Report written to {str(rf)}")

    return_dict = {
        "out_file": str(of),
        # "report_file": str(rf),
        "report": popup_report,
    }
    # print(return_dict["report"])
    return return_dict
    # return json.dumps(return_dict)


def _finalize_format(results, cfg):
    if int(cfg.get("DateFormat", 0)):
        date_col = "Date (YYYY-MM-DD)"
    else:
        date_col = "Date (MM/DD/YYYY)"

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
        col_order += ["System Uncertainty (+/-%)", "Field Uncertainty (+/-%)"]

    return results[col_order]


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


def run_mp(input_data, cfg, max_workers, from_gui):

    future_to_row = {}
    results = {}
    ghi_rad_u, dni_rad_u, dhi_rad_u = extract_rad_uncertainty(cfg)
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # for row_ind, row in tqdm(
        #     input_data.iterrows(), total=len(input_data), desc=input_file.stem
        # ):
        for row_ind, row in input_data.iterrows():
            data = _row_to_data(row, cfg, ghi_rad_u, dni_rad_u, dhi_rad_u)
            future = executor.submit(Uprocess, data, pressure=820, temp=11)
            future_to_row[future] = row_ind

        # print("Collecting outputs...")
        nun_to_run = len(future_to_row)
        # for future in tqdm(as_completed(future_to_row), total=nun_to_run):
        for ind, future in enumerate(as_completed(future_to_row), start=1):
            row_ind = future_to_row.pop(future)
            data = future.result()
            results[row_ind] = data.as_result_dict()
            if from_gui:
                print(int(ind / nun_to_run * 100))

    results = pd.DataFrame(results).T.sort_index()
    return results


def run_sp(input_data, cfg, from_gui):
    results = {}
    ghi_rad_u, dni_rad_u, dhi_rad_u = extract_rad_uncertainty(cfg)
    # for row_ind, row in tqdm(
    #     input_data.iterrows(), total=len(input_data), desc=input_file.stem
    # ):
    nun_to_run = len(input_data)
    for ind, (row_ind, row) in enumerate(input_data.iterrows(), start=1):
        data = _row_to_data(row, cfg, ghi_rad_u, dni_rad_u, dhi_rad_u)
        data = Uprocess(data, pressure=820, temp=11)
        results[row_ind] = data.as_result_dict()
        if from_gui:
            print(int(ind / nun_to_run * 100))

    results = pd.DataFrame(results).T.sort_index()
    return results


# python -c "import json; from suni.cli import process_from_config; fh = open('sample_config.json'); cfg = json.load(fh); fh.close(); process_from_config(cfg)"
