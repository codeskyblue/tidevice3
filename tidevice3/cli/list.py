#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Fri Jan 05 2024 18:10:01 by codeskyblue
"""
from __future__ import annotations

from typing import Optional

import click
from pydantic import BaseModel
from pymobiledevice3 import usbmux
from pymobiledevice3.cli.cli_common import print_json
from pymobiledevice3.lockdown import create_using_usbmux, usbmux

from tidevice3.cli.cli_common import cli, gcfg


@cli.command(name="list")
@click.option("-u", "--usb", is_flag=True, help="show only usb devices")
@click.option("-n", "--network", is_flag=True, help="show only network devices")
def cli_list(usb: bool, network: bool):
    """list connected devices"""
    devices = list_devices(usb, network, gcfg.usbmux_address)
    print_json([d.model_dump() for d in devices], colored=gcfg.color)


class DeviceShortInfo(BaseModel):
    BuildVersion: str
    ConnectionType: Optional[str]
    DeviceClass: str
    DeviceName: str
    Identifier: str
    ProductType: str
    ProductVersion: str


def list_devices(
    usb: bool, network: bool, usbmux_address: Optional[str] = None
) -> list[DeviceShortInfo]:
    connected_devices = []
    for device in usbmux.list_devices(usbmux_address=usbmux_address):
        udid = device.serial

        if usb and not device.is_usb:
            continue

        if network and not device.is_network:
            continue

        lockdown = create_using_usbmux(
            udid,
            autopair=False,
            connection_type=device.connection_type,
            usbmux_address=usbmux_address,
        )
        info = DeviceShortInfo.model_validate(lockdown.short_info)
        connected_devices.append(info)
    return connected_devices
