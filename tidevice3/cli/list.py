#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Fri Jan 05 2024 18:10:01 by codeskyblue
"""
from __future__ import annotations

import unicodedata
from typing import Optional

import click
from pydantic import BaseModel
from pymobiledevice3 import usbmux
from pymobiledevice3.cli.cli_common import print_json
from pymobiledevice3.lockdown import create_using_usbmux, usbmux

from tidevice3.cli.cli_common import cli, gcfg


def display_length(s: str):
    length = 0
    for char in s:
        if unicodedata.east_asian_width(char) in ('F', 'W'):
            length += 2
        else:
            length += 1
    return length


def ljust(s, length: int):
    s = str(s)
    return s + ' ' * (length - display_length(s))


def print_dict_as_table(infos: list[DeviceShortInfo]):
    """
    Output as format
    ----------------------------------------
    Identifier                DeviceName ProductType ProductVersion ConnectionType
    00000000-1234567890123456 MIMM       iPhone13,3  17.2           USB
    """
    headers = ["Identifier", "DeviceName", "ProductType", "ProductVersion", "ConnectionType"]
    header_lens = []
    for header in headers:
        max_len = max([display_length(str(getattr(info, header))) for info in infos])
        header_lens.append(max(max_len, len(header)))
    rows = []
    # print header
    sep = "  "
    for header, header_len in zip(headers, header_lens):
        rows.append(ljust(header, header_len))
    print(sep.join(rows))
    # print rows
    for info in infos:
        rows = []
        for header, header_len in zip(headers, header_lens):
            rows.append(ljust(getattr(info, header), header_len))
        print(sep.join(rows))
        

@cli.command(name="list")
@click.option("-u", "--usb", is_flag=True, help="show only usb devices")
@click.option("-n", "--network", is_flag=True, help="show only network devices")
@click.option("--json", is_flag=True, help="output as json format")
def cli_list(usb: bool, network: bool, json: bool):
    """list connected devices"""
    devices = list_devices(usb, network, gcfg.usbmux_address)
    if json:
        print_json([d.model_dump() for d in devices], colored=gcfg.color)
    else:
        print_dict_as_table(devices)


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
