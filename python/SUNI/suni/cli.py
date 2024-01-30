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
from suni.utilities import (
    format_date,
    convert_to_year_first,
    compute_parameter_stats,
)


PYRANOMETER_UNCERTAINTY = {"A": 2.4, "B": 5.2, "C": 11.9}
PYRANOMETER_CAL_DEFAULT = {"A": 2, "B": 3, "C": 4}
PYRHELIOMETER_UNCERTAINTY = {"A": 0.9, "B": 2.2, "C": 7.4}
PYRHELIOMETER_CAL_DEFAULT = {"A": 0.8, "B": 1, "C": 3.5}


def _data_from_ini(fp):
    cfg = configparser.ConfigParser()
    cfg.read(config)
    return dict(cfg.items("SUNI"))


def _data_from_json(fp):
    with open(fp, "r") as fh:
        data = json.load(fh)
    return data


def _add_inst_uncertainties(config):
    param_to_values = {
        "GHI": (PYRANOMETER_UNCERTAINTY, PYRANOMETER_CAL_DEFAULT),
        "DNI": (PYRHELIOMETER_UNCERTAINTY, PYRHELIOMETER_CAL_DEFAULT),
        "DHI": (PYRANOMETER_UNCERTAINTY, PYRANOMETER_CAL_DEFAULT),
    }
    for param, (uncert, defaults) in param_to_values.items():
        rad_uncertainty_key = f"{param}radUncert"
        if rad_uncertainty_key in config:
            continue
        inst_class = config[f"{param}class"]
        inst_uncert = config.get(f"{param}classUncert", uncert[inst_class])
        cal_uncert = config.get(f"{param}calUncert", defaults[inst_class])
        config[rad_uncertainty_key] = sqrt(inst_uncert**2 + cal_uncert**2)

    return config


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
    cfg = _add_inst_uncertainties(cfg)
    max_workers = cfg.get("max_workers", 1)
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
        out = run_mp(input_data, input_file, cfg, max_workers)
    else:
        out = run_sp(input_data, input_file, cfg)

    results = out[0]
    int_cols = ["qcGHI", "qcDNI", "qcDHI", "uCode", "SQCcode"]
    results[int_cols] = results[int_cols].astype(int)
    results = pd.concat([input_data, results], axis=1)
    results = _finalize_format(results, cfg)
    results.to_csv(of, index=False, float_format="%.1f")
    # print(f"Results written to {str(of)}")

    rf = Path(of).parent / f"{input_file.stem}_Report.txt"
    standard_report = _compile_standard_report(
        input_data, cfg, out, input_file, of, proc_start_time
    )
    with open(rf, "w") as fh:
        fh.write(standard_report)
    # print(standard_report)
    # print(f"Report written to {str(rf)}")

    return_dict = {
        "out_file": str(of),
        # "report_file": str(rf),
        "report": _compile_popup_report(input_data, cfg, out, input_file, of),
    }
    # print(return_dict["report"])
    return return_dict
    # return json.dumps(return_dict)


def _finalize_format(results, cfg):
    if cfg.get("DateFormat"):
        results["DATE"] = results["DATE"].map(convert_to_year_first)
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
    if cfg.get("ExtendedRpt"):
        col_order += ["System Uncertainty (+/-%)", "Field Uncertainty (+/-%)"]

    return results[col_order]


def _extract_time_from_input_data(row):
    month, day, year = map(int, row["DATE"].split("/"))
    hour, minute = map(int, row["MST"].split(":"))
    return year, month, day, hour, minute


def _compile_popup_report(input_data, cfg, out, input_file, of):
    (
        results,
        U95GHIsum,
        U95DNIsum,
        U95DHIsum,
        UFieldsum,
        Uradssum,
        UoSYSsum,
        UoSYSAbssum,
        U95GHIsumSq,
        U95DNIsumSq,
        U95DHIsumSq,
        UFieldsumSq,
        UradssumSq,
        UoSYSsumSq,
        UoSYSAbssumSq,
        counts,
        n_valid,
        sun_up_count,
        field_uncertainty_count,
    ) = out

    start_time = _extract_time_from_input_data(input_data.iloc[0])
    end_time = _extract_time_from_input_data(input_data.iloc[-1])

    sq_max = counts[ErrorCode.QC_MAX]
    lines = [
        f"Uncertainty Processing Report for {input_file.name} "
        f"{cfg['StationID']}\n",
        f"Beginning: {format_date(*start_time[:3], cfg.get('DateFormat'))} "
        f"{start_time[3]}:{start_time[4]:02d}, "
        f"Ending: {format_date(*end_time[:3], cfg.get('DateFormat'))} "
        f"{end_time[3]}:{end_time[4]:02d}, "
        f"Data records: {len(results):d}",
        f"Total eligible records: {n_valid:d} ({n_valid/len(results):.1%})",
        f"Exceeded SERIQC max: {sq_max:d} ({sq_max/len(results):.1%})\n",
    ]

    out_params = ["GHI mean U95", "DNI mean U95", "DHI mean U95"]
    sums = [U95GHIsum, U95DNIsum, U95DHIsum]
    sum_sqs = [U95GHIsumSq, U95DNIsumSq, U95DHIsumSq]
    for param, sum_, sum_sq in zip(out_params, sums, sum_sqs):
        mean, std = compute_parameter_stats(
            sum_, sum_sq, sun_up_count, n_valid
        )
        lines.append(
            f"{param}: +/-{mean:.2f}% | Standard deviation: {std:.2f}"
        )

    if cfg.get("ExtendedRpt"):
        lines.append("")
        out_params = [
            "Urads Uncertainty Mean",
            "System Uncertainty Mean",
            "Field Uncertainty Mean",
        ]
        sums = [Uradssum, UoSYSAbssum, UFieldsum]
        sum_sqs = [UradssumSq, UoSYSAbssumSq, UFieldsumSq]
        for param, sum_, sum_sq in zip(out_params, sums, sum_sqs):
            # mean, std = compute_parameter_stats(
            #     sum_, sum_sq, sun_up_count, n_valid
            # )
            mean = (sum_ / sun_up_count) if sun_up_count > 0 else -9900
            lines.append(f"{param}: +/-{mean:.2f}%")

    return "\n".join(lines)


def _compile_standard_report(
    input_data, cfg, out, input_file, of, proc_start_time
):
    (
        results,
        U95GHIsum,
        U95DNIsum,
        U95DHIsum,
        UFieldsum,
        Uradssum,
        UoSYSsum,
        UoSYSAbssum,
        U95GHIsumSq,
        U95DNIsumSq,
        U95DHIsumSq,
        UFieldsumSq,
        UradssumSq,
        UoSYSsumSq,
        UoSYSAbssumSq,
        counts,
        n_valid,
        sun_up_count,
        field_uncertainty_count,
    ) = out

    start_time = _extract_time_from_input_data(input_data.iloc[0])
    end_time = _extract_time_from_input_data(input_data.iloc[-1])
    proc_date = proc_start_time.strftime(
        "%Y-%m-%d %H:%M" if cfg.get("DateFormat") else "%m/%d/%Y %H:%M"
    )

    lines = [
        f"Uncertainty Processing Report for {input_file.name}",
        # f"{cfg['StationID']}\n",
        f"Processing date: {proc_date}",
        f"From {format_date(*start_time[:3], cfg.get('DateFormat'))} "
        f"{start_time[3]}:{start_time[4]:02d} "
        f"to {format_date(*end_time[:3], cfg.get('DateFormat'))} "
        f"{end_time[3]}:{end_time[4]:02d} "
        f"({cfg['Interval']}-minute interval)\n",
        "System Configuration:",
    ]

    out_params = ["GHI", "DNI", "DHI"]
    for param in out_params:
        s_n = cfg[f"{param}id"]
        inst_class = cfg[f"{param}class"]
        class_uncert = cfg[f"{param}classUncert"]
        cal_uncert = cfg[f"{param}calUncert"]
        cal_due = cfg[f"{param}calDate"]
        due = cfg[f"{param}dueDate"]
        rad_uncert = cfg[f"{param}radUncert"]
        line = " | ".join(
            [
                f"{param}: s/n {s_n}",
                f"Class: {inst_class}",
                f"Class Uncert: +/-{class_uncert:.2f}%",
                f"Cal Uncert: +/-{cal_uncert:.2f}%",
                f"Cal Date: {cal_due}",
                f"Due Date: {due}",
                f"Radiometer Uncert: +/-{rad_uncert:.2f}%",
            ]
        )
        lines.append(line)

    three_comp = (
        len(results) - counts[ErrorCode.SERIQC] - counts[ErrorCode.THREE_COMP]
    )
    sq_max = counts[ErrorCode.QC_MAX]
    high_zen = counts[ErrorCode.HIGH_ZENITH]
    low_dni = counts[ErrorCode.LOW_DNI]
    math_invalid = counts[ErrorCode.ETR] + counts[ErrorCode.K_SPACE]

    lines += [
        f"SERI QC Max: {cfg['MaxQC']}",
        f"Zenith Angle Max: {cfg['MaxZEN']:.1f}",
        f"DNI Min: {cfg['MinDNI']:.1f}",
        f"System Uncertainty Max: {cfg['MaxSysUncert']}\n",
        f"Input Data Records: {len(results):d}",
        f"Three-component records: {three_comp:d} ({three_comp/len(results):.1%})",
        f"Above SERIQC Max: {sq_max:d} ({sq_max/len(results):.1%})",
        f"Above Zenith Angle Max: {high_zen:d} ({high_zen/len(results):.1%})",
        f"Below DNI Minimum: {low_dni:d} ({low_dni/len(results):.1%})",
        f"Mathematically Invalid: {math_invalid:d} ({math_invalid/len(results):.1%})",
        f"Total Eligible Uncertainty Records: {n_valid:d} ({n_valid/len(results):.1%})\n",
    ]

    sums = [U95GHIsum, U95DNIsum, U95DHIsum]
    sum_sqs = [U95GHIsumSq, U95DNIsumSq, U95DHIsumSq]
    for param, sum_, sum_sq in zip(out_params, sums, sum_sqs):
        mean, std = compute_parameter_stats(
            sum_, sum_sq, sun_up_count, n_valid
        )
        lines.append(
            f"{param} Mean U95: +/-{mean:.1f}% | Standard deviation: {std:.1f}"
        )

    if cfg.get("ExtendedRpt"):
        lines.append("")
        out_params = [
            "Urads Uncertainty Mean: +/-",
            "System Uncertainty Mean: ",
            "Field Uncertainty Mean: +/-",
        ]
        sums = [Uradssum, UoSYSAbssum, UFieldsum]
        sum_sqs = [UradssumSq, UoSYSAbssumSq, UFieldsumSq]
        for param, sum_, sum_sq in zip(out_params, sums, sum_sqs):
            # mean, std = compute_parameter_stats(
            #     sum_, sum_sq, sun_up_count, n_valid
            # )
            mean = (sum_ / sun_up_count) if sun_up_count > 0 else -9900
            lines.append(f"{param}{mean:.2f}%")

    return "\n".join(lines)


def _compile_test_report(cfg, out, input_file, of):
    (
        results,
        U95GHIsum,
        U95DNIsum,
        U95DHIsum,
        UFieldsum,
        Uradssum,
        UoSYSsum,
        UoSYSAbssum,
        U95GHIsumSq,
        U95DNIsumSq,
        U95DHIsumSq,
        UFieldsumSq,
        UradssumSq,
        UoSYSsumSq,
        UoSYSAbssumSq,
        counts,
        n_valid,
        sun_up_count,
        field_uncertainty_count,
    ) = out
    lines = [
        f'Station,{cfg.get("StationID")}',
        f"Total_records,{len(results)}",
        f"Total_sunup_records,{sun_up_count}",
        f"Total_valid_records,{n_valid}",
        f"Total_invalid_records,{len(results)-n_valid}",
        "Meas,Ur",
        f'GHI,{cfg["GHIradUncert"]}',
        f'DNI,{cfg["DNIradUncert"]}',
        f'DHI,{cfg["DHIradUncert"]}\n',
        f"Input_file,{input_file.name}",
        # f"Config_file,{Path(config).name}",
        f"Output_file,{str(of)}\n",
        "Code,count",
    ]
    for code, count in enumerate(counts):
        # fh.write(f"{code:<4d},{count:d}\n")
        lines.append(f"{code:d},{count:d}")

    out_params = ["U95GHI", "U95DNI", "U95DHI", "UoSys", "UoSysAbs", "Ufield"]
    sums = [U95GHIsum, U95DNIsum, U95DHIsum, UoSYSsum, UoSYSAbssum, UFieldsum]
    sum_sqs = [
        U95GHIsumSq,
        U95DNIsumSq,
        U95DHIsumSq,
        UoSYSsumSq,
        UoSYSAbssumSq,
        UFieldsumSq,
    ]
    lines.append("\nParameter,Mean,Stdev")
    for param, sum_, sum_sq in zip(out_params, sums, sum_sqs):
        mean, std = compute_parameter_stats(
            sum_, sum_sq, sun_up_count, n_valid
        )

        # fh.write(f"{param:<9},{mean:8.2f},{std:8.2f}\n")
        lines.append(f"{param},{mean:.2f},{std:.2f}")

    pct_field_uncertainty_count = (
        (field_uncertainty_count / sun_up_count * 100)
        if sun_up_count > 0
        else -9900
    )
    lines.append(f"PctUfield,{pct_field_uncertainty_count:.2f},")
    return "\n".join(lines)


def _extract_rad_uncertainty(cfg):
    # TODO: The defaults for these need to be implemented via Aron's equation
    ghi = float(cfg.get("GHIradUncert", 1))
    dni = float(cfg.get("DNIradUncert", 1))
    dhi = float(cfg.get("DHIradUncert", 1))
    return ghi, dni, dhi


def _extract_irri(row):
    irri = row[["GHI", "DNI", "DHI"]].astype(float)
    irri[irri < -9900] *= -1
    return irri


def run_mp(input_data, input_file, cfg, max_workers):
    U95GHIsum = (
        U95DNIsum
    ) = U95DHIsum = UFieldsum = Uradssum = UoSYSsum = UoSYSAbssum = 0
    U95GHIsumSq = (
        U95DNIsumSq
    ) = U95DHIsumSq = UFieldsumSq = UradssumSq = UoSYSsumSq = 0
    UoSYSAbssumSq = 0
    counts = [0] * len(ErrorCode)
    n_valid = sun_up_count = field_uncertainty_count = 0

    future_to_row = {}
    results = {}
    ghi_rad_u, dni_rad_u, dhi_rad_u = _extract_rad_uncertainty(cfg)
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # for row_ind, row in tqdm(
        #     input_data.iterrows(), total=len(input_data), desc=input_file.stem
        # ):
        for row_ind, row in input_data.iterrows():
            year, month, day, hour, minute = _extract_time_from_input_data(row)
            ghi, dni, dhi = _extract_irri(row)
            data = uDat(
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
            future = executor.submit(Uprocess, data, pressure=820, temp=11)
            future_to_row[future] = row_ind

        # print("Collecting outputs...")
        nun_to_run = len(future_to_row)
        # for future in tqdm(as_completed(future_to_row), total=nun_to_run):
        for future in as_completed(future_to_row):
            row_ind = future_to_row.pop(future)
            data = future.result()
            results[row_ind] = {
                "qcGHI": data.qcGHI,
                "qcDNI": data.qcDNI,
                "qcDHI": data.qcDHI,
                "uCode": data.uCode,
                "U95GHI": data.U95GHI,
                "U95DNI": data.U95DNI,
                "U95DHI": data.U95DHI,
                "UoSys": data.Usys,
                "UoSysAbs": data.UsysAbs,
                "Ufield": data.Ufield,
                "zen": data.zen,
                "ETR": data.ETR,
                "ETRn": data.ETRn,
                "kt": data.kt,
                "kn": data.kn,
                "kd": data.kd,
                "SQCcode": data.SQCcode,
            }

            U95GHIsum += data.U95GHI or 0
            U95DNIsum += data.U95DNI or 0
            U95DHIsum += data.U95DHI or 0
            UFieldsum += data.Ufield or 0
            Uradssum += data.Urads or 0
            UoSYSsum += data.Usys or 0
            UoSYSAbssum += data.UsysAbs or 0

            U95GHIsumSq += (data.U95GHI or 0) ** 2
            U95DNIsumSq += (data.U95DNI or 0) ** 2
            U95DHIsumSq += (data.U95DHI or 0) ** 2
            UFieldsumSq += (data.Ufield or 0) ** 2
            UradssumSq += (data.Urads or 0) ** 2
            UoSYSsumSq += (data.Usys or 0) ** 2
            UoSYSAbssumSq += (data.UsysAbs or 0) ** 2

            counts[data.uCode] += 1
            sun_up_count += data.zen < 90
            field_uncertainty_count += (data.Ufield or 0) > 0
            if data.uCode == ErrorCode.VALID:
                n_valid += 1

    results = pd.DataFrame(results).T.sort_index()
    return (
        results,
        U95GHIsum,
        U95DNIsum,
        U95DHIsum,
        UFieldsum,
        Uradssum,
        UoSYSsum,
        UoSYSAbssum,
        U95GHIsumSq,
        U95DNIsumSq,
        U95DHIsumSq,
        UFieldsumSq,
        UradssumSq,
        UoSYSsumSq,
        UoSYSAbssumSq,
        counts,
        n_valid,
        sun_up_count,
        field_uncertainty_count,
    )


def run_sp(input_data, input_file, cfg):
    U95GHIsum = (
        U95DNIsum
    ) = U95DHIsum = UFieldsum = Uradssum = UoSYSsum = UoSYSAbssum = 0
    U95GHIsumSq = (
        U95DNIsumSq
    ) = U95DHIsumSq = UFieldsumSq = UradssumSq = UoSYSsumSq = 0
    UoSYSAbssumSq = 0
    counts = [0] * len(ErrorCode)
    n_valid = sun_up_count = field_uncertainty_count = 0

    results = {}
    ghi_rad_u, dni_rad_u, dhi_rad_u = _extract_rad_uncertainty(cfg)
    # for row_ind, row in tqdm(
    #     input_data.iterrows(), total=len(input_data), desc=input_file.stem
    # ):
    for row_ind, row in input_data.iterrows():
        year, month, day, hour, minute = _extract_time_from_input_data(row)
        ghi, dni, dhi = _extract_irri(row)
        data = uDat(
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
        data = Uprocess(data, pressure=820, temp=11)
        results[row_ind] = {
            "qcGHI": data.qcGHI,
            "qcDNI": data.qcDNI,
            "qcDHI": data.qcDHI,
            "uCode": data.uCode,
            "U95GHI": data.U95GHI,
            "U95DNI": data.U95DNI,
            "U95DHI": data.U95DHI,
            "UoSys": data.Usys,
            "UoSysAbs": data.UsysAbs,
            "Ufield": data.Ufield,
            "zen": data.zen,
            "ETR": data.ETR,
            "ETRn": data.ETRn,
            "kt": data.kt,
            "kn": data.kn,
            "kd": data.kd,
            "SQCcode": data.SQCcode,
        }

        U95GHIsum += data.U95GHI or 0
        U95DNIsum += data.U95DNI or 0
        U95DHIsum += data.U95DHI or 0
        UFieldsum += data.Ufield or 0
        Uradssum += data.Urads or 0
        UoSYSsum += data.Usys or 0
        UoSYSAbssum += data.UsysAbs or 0

        U95GHIsumSq += (data.U95GHI or 0) ** 2
        U95DNIsumSq += (data.U95DNI or 0) ** 2
        U95DHIsumSq += (data.U95DHI or 0) ** 2
        UFieldsumSq += (data.Ufield or 0) ** 2
        UradssumSq += (data.Urads or 0) ** 2
        UoSYSsumSq += (data.Usys or 0) ** 2
        UoSYSAbssumSq += (data.UsysAbs or 0) ** 2

        counts[data.uCode] += 1
        sun_up_count += data.zen < 90
        field_uncertainty_count += (data.Ufield or 0) > 0
        if data.uCode == ErrorCode.VALID:
            n_valid += 1

    results = pd.DataFrame(results).T.sort_index()
    return (
        results,
        U95GHIsum,
        U95DNIsum,
        U95DHIsum,
        UFieldsum,
        Uradssum,
        UoSYSsum,
        UoSYSAbssum,
        U95GHIsumSq,
        U95DNIsumSq,
        U95DHIsumSq,
        UFieldsumSq,
        UradssumSq,
        UoSYSsumSq,
        UoSYSAbssumSq,
        counts,
        n_valid,
        sun_up_count,
        field_uncertainty_count,
    )


# python -c "import json; from suni.cli import process_from_config; fh = open('sample_config.json'); cfg = json.load(fh); fh.close(); process_from_config(cfg)"
