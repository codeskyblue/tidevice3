#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Mon Jan 08 2024 14:50:21 by codeskyblue
"""

import io
import logging
import typing

import click
from pymobiledevice3.lockdown import LockdownClient
from pymobiledevice3.services.dvt.dvt_secure_socket_proxy import DvtSecureSocketProxyService
from pymobiledevice3.services.screenshot import ScreenshotService
from pymobiledevice3.services.dvt.instruments.screenshot import Screenshot

from tidevice3.cli.cli_common import cli, gcfg

logger = logging.getLogger(__name__)

from PIL import Image


def byte2image(data: bytes) -> Image:
    return Image.open(io.BytesIO(data)).convert("RGB")


def screenshot(lockdown_client: LockdownClient) -> Image.Image:
    service_provider = gcfg.get_service_provider()
    if gcfg.major_version >= 17:
        with DvtSecureSocketProxyService(lockdown=service_provider) as dvt:
            png_data = Screenshot(dvt).get_screenshot()
    else:
        png_data = ScreenshotService(lockdown_client).take_screenshot()
    return byte2image(png_data)
    

@cli.command("screenshot")
@click.argument("out", type=click.File("wb"))
def cli_screenshot(out: typing.BinaryIO):
    """get device screenshot"""
    lockdown_client = gcfg.get_lockdown_client()
    screenshot(lockdown_client).save(out)
