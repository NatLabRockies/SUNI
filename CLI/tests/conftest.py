# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name
"""Fixtures for use across all tests."""
import os
import shutil
from pathlib import Path

import click
import pytest
from click.testing import CliRunner


LOGGING_META_FILES = {"log.py", "exceptions.py", "warnings.py"}


@pytest.fixture
def assert_message_was_logged(caplog):
    """Assert that a particular (partial) message was logged."""
    caplog.clear()

    def assert_message(msg, log_level=None, clear_records=False):
        """Assert that a message was logged."""
        assert caplog.records

        for record in caplog.records:
            if msg in record.message:
                break
        else:
            raise AssertionError(f"{msg!r} not found in log records")

        # record guaranteed to be defined b/c of "assert caplog.records"
        # pylint: disable=undefined-loop-variable
        if log_level:
            assert record.levelname == log_level
        assert record.filename not in LOGGING_META_FILES
        assert record.funcName != "__init__"
        assert "gaps" in record.name

        if clear_records:
            caplog.clear()

    return assert_message


@pytest.fixture(scope="module")
def cli_runner():
    """Cli runner helper utility."""
    return CliRunner()


@pytest.fixture(autouse=True)
def save_test_dir():
    """Return to the starting dir after running a test.

    In particular, persisting the batch dir change that happens during
    a BatchJob run can mess up downstream tests.
    """
    previous_dir = os.getcwd()
    yield
    os.chdir(previous_dir)


@pytest.fixture
def test_ctx(tmp_path):
    """Test context."""
    with click.Context(click.Command("run"), obj={}) as ctx:
        ctx.obj["NAME"] = "test"
        ctx.obj["TMP_PATH"] = tmp_path
        ctx.obj["VERBOSE"] = False
        yield ctx


@pytest.fixture
def repository_dir():
    """str: Repository dir"""
    return Path(__file__).parent.parent


@pytest.fixture
def tests_dir(repository_dir):
    """str: Repository dir"""
    return repository_dir / "tests"


@pytest.fixture
def test_data_dir(tests_dir):
    """Return `Path` object to test data dir."""
    return tests_dir / "data"


@pytest.fixture
def test_data_basic_run_dir(test_data_dir):
    """Return `Path` object to basic run test data dir."""
    return test_data_dir / "basic_run"


@pytest.fixture
def tmp_cwd(tmp_path):
    """Change working dir to temporary dir."""
    original_directory = os.getcwd()
    try:
        os.chdir(tmp_path)
        yield tmp_path
    finally:
        os.chdir(original_directory)


def pytest_configure(config):
    """Configure tests."""

    config.addinivalue_line(  # cspell:disable-line
        "markers", "integration: mark test and an integration test"
    )
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_addoption(parser):
    """Add a command line option for pytest"""
    parser.addoption(
        "--slow", action="store_true", default=False, help="run slow tests"
    )
    parser.addoption(
        "--save",
        action="store_true",
        default=False,
        help="store benchmarking results on disk",
    )


def pytest_collection_modifyitems(config, items):
    """Skip slow tests unless user specifies `pytest --slow ...`"""
    if config.getoption("--slow"):
        # --slow given in cli: do not skip slow tests
        return

    skip_slow = pytest.mark.skip(reason="need --slow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
