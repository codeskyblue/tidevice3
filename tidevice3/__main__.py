#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Fri Jan 05 2024 17:47:29 by codeskyblue
"""
import logging
import sys

import click

import tidevice3.cli.list as _
import tidevice3.cli.developer as _
from tidevice3.cli.cli_common import cli

logger = logging.getLogger(__name__)


def main():
    try:
        cli(auto_envvar_prefix='TIDEVICE3')
    except Exception as e:
        click.echo(f"Error: {type(e)} {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()