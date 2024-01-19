#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Mon Jan 08 2024 14:50:21 by codeskyblue
"""

import logging
import typing

import click
from pymobiledevice3.lockdown import LockdownClient

from tidevice3.api import screenshot, screenshot_png
from tidevice3.cli.cli_common import cli, pass_rsd

logger = logging.getLogger(__name__)


@cli.command("screenshot")
@click.argument("out", type=click.File("wb"))
@pass_rsd
def cli_screenshot(service_provider: LockdownClient, out: typing.BinaryIO):
    """get device screenshot"""
    if out.name.endswith(".png"):
        out.write(screenshot_png(service_provider))
    else:
        im = screenshot(service_provider)
        im.save(out)
