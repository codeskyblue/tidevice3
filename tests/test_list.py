#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Fri Jan 05 2024 18:56:00 by codeskyblue
"""

from click.testing import CliRunner

import tidevice3.cli.list as _
from tidevice3.cli.cli_common import cli


def test_list():
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0, result.output
