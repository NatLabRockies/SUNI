# fmt: off
from enum import IntEnum
from pathlib import Path
from functools import lru_cache

import pandas as pd
import numpy as np

# Add plotting options

HEADER_VARIABLES = ['month'] + ['Kn_max', 'Kt_max', 'left_shape', 'left_position', 'right_shape', 'right_position']*3

HEADER_AIRMASS = [None] + ['low']*6 + ['medium']*6 + ['high']*6

QA0_MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP",
              "OCT", "NOV", "DEC"]


class QA0FileError(Exception):
    """Exception to indicate problems with QA0 file."""


class AirMassRegime(IntEnum):
    """Integer flag representing the air mass regime. """
    LOW = 1
    MEDIUM = 2
    HIGH = 3

    def __str__(self):
        return f"{self.name.lower()}"

    @classmethod
    def from_value(cls, value):
        """Convert an air mass value to an air mass regime enum option.

        Air mass regimes are defined as follows:

            - HIGH = air mass > 2.5
            - MEDIUM = 1.25 < air mass <= 2.5
            - LOW <= 1.25

        Parameters
        ----------
        value : float
            Air mass value.

        Returns
        -------
        AirMassRegime
            AirMassRegime enum option.
        """
        if value > 2.5:
            return cls.HIGH
        if value > 1.25:
            return cls.MEDIUM
        return cls.LOW


@lru_cache(maxsize=128)
def read_qa0(filename):
    """
    Read a QA-zero (.QA0) file created by QAFIT and used by NLR-QA.

    Parameters
    ----------
    filename : path-like
        Filename of the file to read.

    Returns
    -------
    data : DataFrame
        DataFrame with specification of the QAFit boundaries.
    meta : dict
        Dictionary of the site metadata in the file. The dictionary contains
        the keys: {'site_identifier', 'latitude', 'longitude', 'tz'}.
    """
    with open(filename) as fbuf:
        meta = {}
        meta['site_identifier'] = fbuf.readline().split(':')[1].strip()
        meta['latitude'] = float(fbuf.readline().split(':')[1].strip())
        meta['longitude'] = float(fbuf.readline().split(':')[1].strip())
        meta['tz'] = float(fbuf.readline().split(':')[1].strip())

        # skip the next 5 lines which contain the column information
        [next(fbuf) for _ in range(5)]

        def _split_line(line):
            """Split individual data lines into lists."""
            # Standardize the column seperator to be slash (/)
            line = line.strip().replace(': ', '/').replace('-', '/').\
                replace('; ', '/').replace(' ', '/')
            return line.split('/')
        # parse the data section
        data_lines = [_split_line(fbuf.readline()) for _ in range(12)]

        columns = [HEADER_VARIABLES, HEADER_AIRMASS]
        data = pd.DataFrame(data_lines, columns=columns)
        data = data.set_index(('month', None))
        data.columns = data.columns.set_names(
            ['variable', 'airmass'])

        data = data.astype(int)
        data = data.replace(0, np.nan)

        # parse defautl configuration section if present
        next(fbuf)  # skip empty line
        next(fbuf)  # skip default configuration line if present
        while True:
            line = fbuf.readline()
            if line == '':
                break
            else:
                meta[line.split(':')[0].strip()] = line.split(':')[1].strip()

    return data, meta


def read_site_data_for_month(site, qa0_dir, month):
    """Extract data for a particular month from a QA0 file.

    Parameters
    ----------
    site : str
        Name of the site represented by the QA0 file. The QA0 file name
        must be of the format s_<site>.qa0, where <site> is replaced
        by this input.
    qa0_dir : path-like
        Path to directory containing the QA0 file(s) to read.
    month : int
        Integer representing the month of data being requested from the
        Integer representing the month of data being requested from the
        QA0 file (1 = January, 12 = December).
    Returns
    -------
    pandas.Series
        Series containing the QA0 data for the requested month.
    dict
        Dictionary containing meta information (i.e., latitude,
        longitude, timezone, etc.) from the QA0 file.

    Raises
    ------
    FileNotFoundError
        If filepath is not  found on disk.
    QA0FileError
        If the expected month name does not match the month name read
        from the QA0 file.
    """
    filename = Path(qa0_dir) / f"s_{site}.qa0"
    if not filename.exists():
        raise FileNotFoundError(f"{str(filename)} not found")

    data, meta = read_qa0(filename)
    month_data = data.iloc[month - 1]
    if month_data.name != QA0_MONTHS[month - 1]:
        raise QA0FileError(
            f"Expected month {QA0_MONTHS[month - 1]}, found month "
            f"{month_data.name} in {str(filename)}"
        )
    return data.iloc[month - 1], meta


def _int_bin(interval):
    """Compute int_bin"""
    # `int_bin` is an integer from 1 to 4, signifying the place of the digit
    # containing the information in the S_<id>.QA0 file.  If data
    # approximate 1-minute resolution, 1 is chosen; if the resolution
    # approximates 64 minutes, 4 is chosen.
    # ``interval`` should be bounded by 1 and 60.
    res = min(max(interval, 1), 60)
    return int(1.49 + np.log(res) / np.log(4))


def extract_curve_numbers(data, interval, air_mass_regime):
    """Extract Gompertz curve numbers from QA0 month data.

    Parameters
    ----------
    data : pandas.Series
        A pandas Series containing QA0 data for a particular month. See
        :func:`read_site_data_for_month` to extract data in the format
        required by this input.
    interval : int
        The measurement averaging interval (in minutes; 1-60).
    air_mass_regime : AirMassRegime
        AirMassRegime enum option representing the air mass regime.

    Returns
    -------
    left_shape, right_shape : int
        Integer representing the left and right Gompertz curve shape, or
        0 if the shapes were not given in the input QA0 data.
    left_position, right_position : int
        Integer representing the left and right Gompertz curve
        position, or 0 if the positions were not given in the input QA0
        data.

    See Also
    --------
    AirMassRegime :
        Air mass regime enumeration of air mass options.
    read_site_data_for_month :
        Function to parse QA0 file data for a particular month.
    seriqc.gompertz_curves.boundary_from_gompertz_curve :
        Convert shape and position numbers to a curve array.
    """
    data = data.fillna(0).astype(int)
    left_shape = data["left_shape"].iloc[air_mass_regime - 1]
    right_shape = data["right_shape"].iloc[air_mass_regime - 1]

    left_position = data["left_position"].iloc[air_mass_regime - 1]
    int_bin = _int_bin(interval)
    amr = str(air_mass_regime)
    right_position = data["right_position"][amr].iloc[int_bin - 1]

    return left_shape, right_shape, left_position, right_position


def extract_kn_kt(data, interval):
    """Extract Kn and Kt from QA0 data for a particular month.

    Parameters
    ----------
    data : pandas.Series
        A pandas Series containing QA0 data for a particular month. See
        :func:`read_site_data_for_month` to extract data in the format
        required by this input.
    interval : int
        The measurement averaging interval (in minutes; 1-60).

    Returns
    -------
    Kn, Kt : int
        Kn and Kt values from the QA0 file.
    """
    int_bin = _int_bin(interval)
    data = data.fillna(0).astype(int)
    return data["Kn_max"].iloc[0], data["Kt_max"].iloc[int_bin - 1]
