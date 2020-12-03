#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for `pips3` cli."""

from unittest.mock import patch

from click.testing import CliRunner
import pytest

from pips3 import cli
from pips3.exceptions import InvalidConfig

URL = 'http://localhost:9000'
BUCKET = 'somebucket'
PACKAGE = 'pips3'


@patch('pips3.cli.publish_packages')
def test_command_line_interface(publish_mock):
    """Test the CLI."""
    runner = CliRunner()

    result = runner.invoke(cli.main, ['--endpoint', URL, '--bucket', BUCKET])

    assert result.exit_code == 0
    publish_mock.assert_called_with(URL, BUCKET)


@patch('pips3.cli.publish_packages')
def test_command_line_interface_envars(publish_mock, monkeypatch):
    """Test the CLI using envars"""

    monkeypatch.setenv('PIPS3_ENDPOINT', URL)
    monkeypatch.setenv('PIPS3_BUCKET', BUCKET)

    runner = CliRunner()

    result = runner.invoke(cli.main)

    assert result.exit_code == 0
    publish_mock.assert_called_with(URL, BUCKET)


def test_cli_errors(monkeypatch):
    """Test the cli responds to errors"""

    runner = CliRunner()

    result = runner.invoke(cli.main)

    assert result.exit_code != 0
    assert isinstance(result.exception, InvalidConfig)
    assert 'endpoint not specified' in str(result.exception)

    monkeypatch.setenv('PIPS3_ENDPOINT', URL)
    result = runner.invoke(cli.main)

    assert result.exit_code != 0
    assert isinstance(result.exception, InvalidConfig)
    assert 'bucket not specified' in str(result.exception)

    monkeypatch.setenv('PIPS3_BUCKET', URL)
    result = runner.invoke(cli.main)