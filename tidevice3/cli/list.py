#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Fri Jan 05 2024 18:10:01 by codeskyblue
"""
from __future__ import annotations

import click
from pymobiledevice3.cli.cli_common import print_json

from tidevice3.api import list_devices
from tidevice3.cli.cli_common import cli
from tidevice3.utils.common import print_dict_as_table


@cli.command(name="list")
@click.option("-u", "--usb", is_flag=True, help="show only usb devices")
@click.option("-n", "--network", is_flag=True, help="show only network devices")
@click.option("--json", is_flag=True, help="output as json format")
@click.pass_context
def cli_list(ctx: click.Context, usb: bool, network: bool, json: bool):
    """list connected devices"""
    usbmux_address = ctx.obj["usbmux_address"]
    devices = list_devices(usb, network, usbmux_address)
    if json:
        print_json([d.model_dump() for d in devices])
    else:
        headers = ["Identifier", "DeviceName", "ProductType", "ProductVersion", "ConnectionType"]
        print_dict_as_table([d.model_dump() for d in devices], headers)


