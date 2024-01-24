# pylint: disable=too-few-public-methods,invalid-name
"""SUNI data structures"""
from attrs import define
from enum import IntEnum

import numpy as np
import pandas as pd

from seriqc.exec import seriqc_from_file
from suni.merge import merge, system_uncertainty


@define
class uDat:
    """Core uncertainty parameters.
    This dataclass is passed to and from the uncertainty process for a
    single set of measurements. This is the only conduit with the
    calling program.
    """

    stationID: str
    """[INPUT] Station ID for SERIQC (includes access to lat, lon, timezone)"""
    qc0_dir: str
    """[INPUT] Path to QC0 file directory."""
    yr: int
    """[INPUT] Data year timestamp"""
    mo: int
    """[INPUT] Data month timestamp"""
    dy: int
    """[INPUT] Data day timestamp"""
    hr: int
    """[INPUT] Data hour timestamp"""
    mn: int
    """[INPUT] Data minute timestamp"""
    intrvl: int
    """[INPUT] Time step interval of the measurement data"""
    GHI: float
    """[INPUT] GHI measurement"""
    DNI: float
    """[INPUT] DNI measurement"""
    DHI: float
    """[INPUT] DHI measurement"""
    urGHI: float
    """[INPUT] GHI radiometer uncertainty"""
    urDNI: float
    """[INPUT] DNI radiometer uncertainty"""
    urDHI: float
    """[INPUT] DHI radiometer uncertainty"""
    DNImin: float
    """[INPUT] Minimum DNI threshold"""
    Zmax: float
    """[INPUT] Maximum zenith angle threshold"""
    QCmax: int
    """[INPUT] Maximum allowable SERIQC flag"""
    UoSYSmax: int
    """[INPUT] Maximum allowable UoSYS (absolute value)"""

    # return values  # TODO: Default values for these?
    qcGHI: int = None
    """[OUTPUT] SERIQC quality code for GHI"""
    qcDNI: int = None
    """[OUTPUT] SERIQC quality code for DNI"""
    qcDHI: int = None
    """[OUTPUT] SERIQC quality code for DHI"""
    U95GHI: float = None
    """[OUTPUT] Expanded GHI uncertainty"""
    U95DNI: float = None
    """[OUTPUT] Expanded DNI uncertainty"""
    U95DHI: float = None
    """[OUTPUT] Expanded DHI uncertainty"""
    Usys: float = None
    """[OUTPUT] Interim system uncertainty"""
    UsysAbs: float = None
    """[OUTPUT] Absolute values interim system uncertainty"""
    Ufield: float = None
    """[OUTPUT] Interim field uncertainty"""
    Urads: float = None
    """[OUTPUT] Interim radiometer uncertainty"""
    SQCcode: int = None
    """[OUTPUT] SERIQC status return code"""
    uCode: int = None
    """[OUTPUT] Uncertainty status return code"""
    zen: float = None
    """[OUTPUT] Zenith angle"""
    ETR: float = None
    """[OUTPUT] Extraterrestrial solar"""
    ETRn: float = None
    """[OUTPUT] Extraterrestrial direct solar"""
    kt: float = None
    """[OUTPUT] GHI k-space"""
    kn: float = None
    """[OUTPUT] DNI k-space"""
    kd: float = None
    """[OUTPUT] DHI k-space"""


@define
class configDat:
    """Top level structure with sub-structures."""

    station: "station"
    instruments: "instruments"
    files: "files"
    ret_status: "retStatus"
    defaults: "defaults"
    uDat: "uDat"
    statistics: "statistics"
    cancel: bool
    """Flag to interrupt main processing loop"""


@define
class station:
    """Substructure for station and SERIQC info."""

    ID: str
    """Station ID"""
    name: str
    """Station name"""
    latitude: float
    """Station latitude"""
    longitude: float
    """Station longitude"""
    timezone: float
    """Station timezone offset"""


@define
class rad:
    """Substructure for radiometers."""

    SN: str
    """Radiometer station name"""
    mode: str
    measType: str
    calDate: str
    dueDate: str
    rs: float
    Ur: float
    """Radiometer database uncertainty"""
    U95: float
    """Final measurement uncertainty"""
    code: int
    """Uncertainty result code"""


@define
class instruments:
    """Substructure for the three measuring instruments."""

    GHI: "rad"
    """GHI Radiometer"""
    DNI: "rad"
    """DNI Radiometer"""
    DHI: "rad"
    """DHI Radiometer"""


@define
class files:
    """Substructure for input and output files

    Termed ``files`` in Pseudocode from deliverable 6.4.
    """

    input_path: str
    """Path to input file"""
    input_fname: str
    """Name of input file (including extension)"""
    output_path: str
    output_fname: str
    SERIQC_path: str
    extendedRpt: bool
    overwrite_output: bool
    lineCtr: int
    begTime: str
    endTime: str


# // Substructure for input and output files
# Struct files
# 	char input_path[maxPathLength]
# 	char input_fname[maxPathLength]
# 	FILE infile
# 	char output_path[maxPathLength]
# 	char output_fname[maxPathLength]
# 	char SERIQC_path[maxPathLength]
# 	FILE outfile
# 	bool extendedRpt
# 	bool overwrite_output
# 	int  lineCtr
# 	time_t	procTime //system time when processing starts
# 	char begTime[20]  // timestamp of first data record
# 	char endTime[20]  // timestamp of last data record


@define
class retStatus:
    """Substructure for return status and error codes."""

    SERIQC: int
    """SERIQC return status"""
    instUncert: int
    """Instrument uncertainty return status"""
    opUncert: int
    """Operational uncertainty return status"""
    mergeUncert: int
    """Merged uncertainty return status"""


@define
class defaults:
    """Substructure for defaults."""

    max_SERIQC: int
    """Default max SERIQC"""
    min_DNI: float
    """Default minimum DNI"""
    max_zen: int
    """Default maximum zenith angle"""


@define
class stats:
    """Substructure stats for individual instruments."""

    sum: float
    """Sum of values for stdev"""
    sumSq: float
    """Sum of the values squared for stdev"""
    mean: float
    """Calculated mean"""
    stdev: float
    """Calculated standard deviation"""


@define
class statistics:
    """Substructure for statistics for all instruments."""

    Usys: float
    nValid: int
    Sysn: float
    SysSum: float
    Ufn: float
    Ufsum: float
    Urn: float
    Ursum: float
    GHI: "stats"
    DNI: "stats"
    DHI: "stats"
    errorCount: list


class ErrorCode(IntEnum):
    """Enumeration for SROUI error codes."""

    VALID = 0
    SERIQC = 1
    THREE_COMP = 2
    QC_MAX = 4
    HIGH_ZENITH = 5
    LOW_DNI = 6
    ETR = 7
    K_SPACE = 8
    HIGH_UNCERTAINTY = 9
    LIST_SIZE = 10


def Uprocess(data, **kwargs):
    """_summary_

    Parameters
    ----------
    data : :class:`uDat`
        Input/output data struct.

    Returns
    -------
    _type_
        _description_
    """

    (
        data.qcGHI,
        data.qcDNI,
        data.qcDHI,
        data.ETR,
        data.ETRn,
        data.zen,
        data.SQCcode,
    ) = seriqc_from_file(
        data.stationID,
        data.qc0_dir,
        data.yr,
        data.mo,
        data.dy,
        data.hr,
        data.mn,
        data.intrvl,
        data.GHI,
        data.DNI,
        data.DHI,
        **kwargs,
    )

    if data.SQCcode != 0:
        data.uCode = ErrorCode.SERIQC
        return data

    if not is_valid_three_component_record(data.qcGHI):
        data.uCode = ErrorCode.THREE_COMP
        return data

    if data.qcGHI > data.QCmax:
        data.uCode = ErrorCode.QC_MAX
        return data

    if data.zen > data.Zmax:
        data.uCode = ErrorCode.HIGH_ZENITH
        return data

    if data.DNI < data.DNImin:
        data.uCode = ErrorCode.LOW_DNI
        return data

    if data.ETR <= 0 or data.ETRn <= 0:
        data.uCode = ErrorCode.ETR
        return data

    data.kt = data.GHI / data.ETR
    data.kn = data.DNI / data.ETRn
    data.kd = data.DHI / data.ETR

    k_sum = data.kn + data.kd
    if k_sum <= 0:
        data.uCode = ErrorCode.K_SPACE
        return data

    data.Usys = system_uncertainty(data.kt, data.kn, data.kd)
    data.UsysAbs = abs(data.Usys)
    if data.UsysAbs > data.UoSYSmax:
        data.uCode = ErrorCode.HIGH_UNCERTAINTY
        return data

    out = merge(data.kt, data.kn, data.kd, data.urGHI, data.urDNI, data.urDHI)
    data.U95GHI, data.U95DNI, data.U95DHI, data.Ufield, data.Urads = out
    data.uCode = ErrorCode.VALID
    return data


def is_valid_three_component_record(ghi_flag):
    """Determine wether

    Per the 6.4 deliverable::

        Data are valid for passing to the uncertainty calculations if
        the following conditions are met, which represent a valid
        three-component SERIQC flag:

            1.	Flag = 3 OR
            2.	Flag = 9 OR
            3.	Flag >=10 and <= 87 and ((Flag+2) mod 4) < 2.


    Parameters
    ----------
    ghi_flag : int
        SERIQC output GHI flag.

    Returns
    -------
    bool
        Wether the record contains valid three-component data.
    """
    is_3_or_9 = ghi_flag in {3, 9}
    in_valid_range = 10 <= ghi_flag <= 87
    has_valid_remainder = ((ghi_flag + 2) % 4) < 2
    return is_3_or_9 or (in_valid_range and has_valid_remainder)
