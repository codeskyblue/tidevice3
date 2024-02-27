#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Tue Feb 27 2024 10:05:20 by codeskyblue
"""

import click
from pymobiledevice3.lockdown import LockdownClient

from tidevice3.api import app_install
from tidevice3.cli.cli_common import cli, pass_rsd, pass_service_provider


@cli.command("install")
@click.argument("path_or_url")
@pass_service_provider
def cli_install(service_provider: LockdownClient, path_or_url: str):
    """install given .ipa or url, alias for app install"""
    app_install(service_provider, path_or_url)
