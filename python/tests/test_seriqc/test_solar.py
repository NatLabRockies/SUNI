"""Test SERIQC solar utilities."""
from pathlib import Path

import pytest

from seriqc.solar import _rewind_to_previous_hour


def test_rewind_to_previous_hour():
    """Test the `_rewind_to_previous_hour` function"""

    assert _rewind_to_previous_hour(-1, 1, 1, 1, 2000) == (59, 0, 1, 1, 2000)
    assert _rewind_to_previous_hour(-1, 0, 2, 1, 2000) == (59, 23, 1, 1, 2000)
    assert _rewind_to_previous_hour(-1, 0, 1, 1, 2000) == (
        59,
        23,
        31,
        12,
        1999,
    )
    assert _rewind_to_previous_hour(-1, 0, 1, 1, 0) == (59, 23, 31, 12, 99)

    assert _rewind_to_previous_hour(-1, 0, 1, 2, 2000) == (59, 23, 31, 1, 2000)
    assert _rewind_to_previous_hour(-1, 0, 1, 2, 2100) == (59, 23, 31, 1, 2100)

    assert _rewind_to_previous_hour(-1, 0, 1, 3, 2000) == (59, 23, 29, 2, 2000)
    assert _rewind_to_previous_hour(-1, 0, 1, 3, 2100) == (59, 23, 28, 2, 2100)


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
