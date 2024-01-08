#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Mon Jan 08 2024 14:50:21 by codeskyblue
"""

import io
import logging
import typing

import click
import requests
from packaging.version import Version
from pymobiledevice3.remote.remote_service_discovery import RemoteServiceDiscoveryService
from pymobiledevice3.services.dvt.dvt_secure_socket_proxy import DvtSecureSocketProxyService
from pymobiledevice3.services.screenshot import ScreenshotService
from pymobiledevice3.services.dvt.instruments.screenshot import Screenshot

from tidevice3.cli.cli_common import cli, gcfg

logger = logging.getLogger(__name__)

from PIL import Image


def byte2image(data: bytes) -> Image:
    return Image.open(io.BytesIO(data)).convert("RGB")


def screenshot_ge17(udid: str) -> Image.Image:
    """
    screenshot with remote service discovery (ios>=17)
    """
    try:
        resp = requests.get("http://localhost:5555")
        tunnels = resp.json()
        ipv6_address = tunnels.get(udid)
    except requests.RequestException:
        raise RuntimeError("Please run `t3 tunneld` first")

    rsd = RemoteServiceDiscoveryService(ipv6_address)
    try:
        rsd.connect()
    except (TimeoutError, ConnectionError):
        raise RuntimeError("RemoteServiceDiscoveryService connect failed")

    with DvtSecureSocketProxyService(lockdown=rsd) as dvt:
        return byte2image(Screenshot(dvt).get_screenshot())


def screnshot_old() -> Image.Image:
    lockdown_client = gcfg.get_lockdown_client()
    png_data = ScreenshotService(lockdown_client).take_screenshot()
    return byte2image(png_data)


@cli.command("screenshot")
@click.argument("out", type=click.File("wb"))
def screenshot(out: typing.BinaryIO):
    """get device screenshot"""
    lockdown_client = gcfg.get_lockdown_client()
    if Version(lockdown_client.product_version) >= Version("17"):
        img = screenshot_ge17(lockdown_client.udid)
    else:
        img = screnshot_old()
    img.save(out)
