#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Fri Jan 05 2024 18:56:00 by codeskyblue
"""

from click.testing import CliRunner

from tidevice3.cli.cli_common import CLI_GROUPS, cli

runner = CliRunner()

def test_cli_help():
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0, result.output
    
    for subcommand in CLI_GROUPS:
        result = runner.invoke(cli, [subcommand, '--help'])
        assert result.exit_code == 0, (subcommand, result.output)
        