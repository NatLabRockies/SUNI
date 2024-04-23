# -*- coding: utf-8 -*-
"""SUNI report compilation utilities"""
from pathlib import Path

from suni.framework import ErrorCode
from suni.utilities import (
    format_date,
    extract_time_from_input_data,
    compute_parameter_stats,
)


def _counts_from_results(results):
    """Get stat counts from results"""
    counts = results["uCode"].value_counts().to_dict()
    counts = [counts.get(ind, 0) for ind in range(len(ErrorCode))]
    n_valid = (results["uCode"] == ErrorCode.VALID).sum()
    return counts, n_valid


def _add_extended_report(results, lines, n_valid, include_pm=True):
    """Add extended portion on uncertainty to report"""
    lines.append("")
    out_params = [
        "Urads Uncertainty Mean: +/-",
        f"System Uncertainty Mean: {'+/-' if include_pm else ''}",
        "Field Uncertainty Mean: +/-",
    ]
    col_names = ["Urads", "UoSysAbs", "Ufield"]
    for param, col in zip(out_params, col_names):
        param_sum = results[col].sum()
        mean = (param_sum / n_valid) if n_valid > 0 else -9900
        lines.append(f"{param}{mean:.2f}%")
    return lines


def _add_irradiance_stats(results, lines, n_valid, fn=2):
    """Add irradiance summary lines to the report"""
    out_params = ["GHI Mean U95", "DNI Mean U95", "DHI Mean U95"]
    col_names = ["U95GHI", "U95DNI", "U95DHI"]
    for param, col in zip(out_params, col_names):
        param_sum = results[col].sum()
        param_sum_sq = (results[col] ** 2).sum()
        mean, std = compute_parameter_stats(param_sum, param_sum_sq, n_valid)
        lines.append(
            f"{param}: +/-{mean:.{fn}f}% | Standard deviation: {std:.{fn}f}"
        )
    return lines


def _start_end_time(results, date_format):
    """Extract start and end times from the data"""
    start_time = extract_time_from_input_data(results.iloc[0], date_format)
    end_time = extract_time_from_input_data(results.iloc[-1], date_format)
    return start_time, end_time


def compile_popup_report(results, cfg):
    """Compile a short report suitable for a popup window.

    Parameters
    ----------
    results : pd.DataFrame
        DataFrame containing the SERIQC + SUNI results.
    cfg : dict
        User input configuration.

    Returns
    -------
    str
        Compiled report.
    """
    input_fn = Path(cfg["InputFile"]).name

    date_format = int(cfg.get("DateFormat", 0))
    start_time, end_time = _start_end_time(results, date_format)
    counts, n_valid = _counts_from_results(results)
    sq_max = counts[ErrorCode.QC_MAX]

    lines = [
        f"Uncertainty Processing Report for {input_fn} "
        f"{cfg['StationID']}\n",
        f"Beginning: {format_date(*start_time[:3], date_format)} "
        f"{start_time[3]}:{start_time[4]:02d}, "
        f"Ending: {format_date(*end_time[:3], date_format)} "
        f"{end_time[3]}:{end_time[4]:02d}, "
        f"Data records: {len(results):d}",
        f"Total eligible records: {n_valid:d} ({n_valid/len(results):.1%})",
        f"Exceeded SERIQC max: {sq_max:d} ({sq_max/len(results):.1%})\n",
    ]
    lines = _add_irradiance_stats(results, lines, n_valid, fn=2)

    if int(cfg.get("ExtendedRpt", 0)):
        lines = _add_extended_report(results, lines, n_valid, include_pm=True)

    return "\n".join(lines)


def compile_standard_report(results, cfg, proc_start_time):
    """Compile a standard report summary from the results.

    Parameters
    ----------
    results : pd.DataFrame
        DataFrame containing the SERIQC + SUNI results.
    cfg : dict
        User input configuration.
    proc_start_time : datetime.datetime
        Datetime instance corresponding to the time processing started.

    Returns
    -------
    str
        Compiled report.
    """

    input_fn = Path(cfg["InputFile"]).name
    date_format = int(cfg.get("DateFormat", 0))
    start_time, end_time = _start_end_time(results, date_format)
    proc_date = proc_start_time.strftime(
        "%Y-%m-%d %H:%M" if date_format else "%m/%d/%Y %H:%M"
    )
    counts, n_valid = _counts_from_results(results)

    qc0_file = f"s_{cfg['StationID']}.qc0"
    lines = [
        f"Uncertainty Processing Report for {input_fn}",
        f"Station Name: {cfg['StationID']}",
        f"Station ID: {cfg['StationID']}",
        f"QC0 File: {qc0_file}",
        f"Processing date: {proc_date}",
        f"From {format_date(*start_time[:3], date_format)} "
        f"{start_time[3]}:{start_time[4]:02d} "
        f"to {format_date(*end_time[:3], date_format)} "
        f"{end_time[3]}:{end_time[4]:02d} "
        f"({cfg['Interval']}-minute interval)\n",
        "System Configuration:",
    ]

    out_params = ["GHI", "DNI", "DHI"]
    for param in out_params:
        s_n = cfg[f"{param}id"]
        inst_class = cfg[f"{param}class"]
        class_uncertainty = float(cfg[f"{param}classUncert"])
        cal_uncertainty = float(cfg[f"{param}calUncert"])
        cal_due = cfg.get(f"{param}calDate") or "Not specified"
        due = cfg.get(f"{param}dueDate") or "Not specified"
        rad_uncertainty = float(cfg[f"{param}radUncert"])
        line = " | ".join(
            [
                f"{param}: s/n {s_n}",
                f"Class: {inst_class}",
                f"Class Uncert: +/-{class_uncertainty:.2f}%",
                f"Cal Uncert: +/-{cal_uncertainty:.2f}%",
                f"Cal Date: {cal_due}",
                f"Due Date: {due}",
                f"Radiometer Uncert: +/-{rad_uncertainty:.2f}%",
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
        f"Zenith Angle Max: {float(cfg['MaxZEN']):.1f}",
        f"DNI Min: {float(cfg['MinDNI']):.1f}",
        f"System Uncertainty Max: {cfg['MaxSysUncert']}\n",
        f"Input Data Records: {len(results):d}",
        f"Three-component records: "
        f"{three_comp:d} ({three_comp/len(results):.1%})",
        f"Above SERIQC Max: {sq_max:d} ({sq_max/len(results):.1%})",
        f"Above Zenith Angle Max: {high_zen:d} ({high_zen/len(results):.1%})",
        f"Below DNI Minimum: {low_dni:d} ({low_dni/len(results):.1%})",
        f"Mathematically Invalid: "
        f"{math_invalid:d} ({math_invalid/len(results):.1%})",
        f"Total Eligible Uncertainty Records: "
        f"{n_valid:d} ({n_valid/len(results):.1%})\n",
    ]
    lines = _add_irradiance_stats(results, lines, n_valid, fn=2)

    if int(cfg.get("ExtendedRpt", 0)):
        lines = _add_extended_report(results, lines, n_valid, include_pm=False)

    return "\n".join(lines)


def _compile_test_report(cfg, results, input_fn, of):  # pragma: no cover
    """Compile a report used for initial SUNI testing"""

    counts = results["uCode"].value_counts().to_dict()
    counts = [counts.get(ind, 0) for ind in range(len(ErrorCode))]
    sun_up_count = (results["zen"] < 90).sum()
    n_valid = (results["uCode"] == ErrorCode.VALID).sum()

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
        f"Input_file,{input_fn}",
        # f"Config_file,{Path(config).name}",
        f"Output_file,{str(of)}\n",
        "Code,count",
    ]
    for code, count in enumerate(counts):
        # fh.write(f"{code:<4d},{count:d}\n")
        lines.append(f"{code:d},{count:d}")

    out_params = ["U95GHI", "U95DNI", "U95DHI", "UoSys", "UoSysAbs", "Ufield"]
    lines.append("\nParameter,Mean,Stdev")
    for (param,) in out_params:
        param_sum = results[param].sum()
        param_sum_sq = (results[param] ** 2).sum()
        mean, std = compute_parameter_stats(param_sum, param_sum_sq, n_valid)

        # fh.write(f"{param:<9},{mean:8.2f},{std:8.2f}\n")
        lines.append(f"{param},{mean:.2f},{std:.2f}")

    field_uncertainty_count = (results["Ufield"] > 0).sum()
    pct_field_uncertainty_count = (
        (field_uncertainty_count / n_valid * 100) if n_valid > 0 else -9900
    )
    lines.append(f"PctUfield,{pct_field_uncertainty_count:.2f},")
    return "\n".join(lines)
