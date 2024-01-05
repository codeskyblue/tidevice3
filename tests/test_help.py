#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Fri Jan 05 2024 18:56:00 by codeskyblue
"""

from click.testing import CliRunner

import tidevice3.cli.list as _
import tidevice3.cli.developer as _
from tidevice3.cli.cli_common import cli

runner = CliRunner()

def test_cli():
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0, result.output

def test_list():
    result = runner.invoke(cli, ['list', '--help'])
    assert result.exit_code == 0, result.output

def test_developer():
    result = runner.invoke(cli, ['developer', '--help'])
    assert result.exit_code == 0, result.output
