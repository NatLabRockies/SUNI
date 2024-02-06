# -*- coding: utf-8 -*-
"""SUNI framework tests"""
from pathlib import Path

import pytest

from suni.framework import is_valid_three_component_record


def test_is_valid_three_component_record():
    """Test `is_valid_three_component_record` function"""

    assert is_valid_three_component_record(3)
    assert is_valid_three_component_record(9)
    assert is_valid_three_component_record(10)
    assert is_valid_three_component_record(11)
    assert is_valid_three_component_record(14)
    assert is_valid_three_component_record(15)
    assert is_valid_three_component_record(86)
    assert is_valid_three_component_record(87)

    assert not is_valid_three_component_record(0)
    assert not is_valid_three_component_record(1)
    assert not is_valid_three_component_record(4)
    assert not is_valid_three_component_record(8)
    assert not is_valid_three_component_record(12)
    assert not is_valid_three_component_record(13)
    assert not is_valid_three_component_record(16)
    assert not is_valid_three_component_record(17)
    assert not is_valid_three_component_record(88)
    assert not is_valid_three_component_record(89)


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
