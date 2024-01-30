# -*- coding: utf-8 -*-
"""ELM Web scraping utilities tests"""
from pathlib import Path

import pytest



@pytest.mark.parametrize(
    "query, expected_out",
    [
        ("", ""),
        ("1", "1"),
        (" a ", "a"),
        ('1.    "a test"', "a test"),
        (' 1. a test" ', '1. a test"'),
        (' 1. "a test ', "a test"),
        (' 1. "a test" and another ', 'a test" and another'),
        ("A normal query", "A normal query"),
    ],
)
def test_clean_search_query(query, expected_out):
    """Test cleaning google web search query"""



if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])