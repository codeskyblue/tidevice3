#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Fri Jan 05 2024 18:10:32 by codeskyblue
"""
from __future__ import annotations
from functools import lru_cache

import click
from dataclasses import dataclass
from pymobiledevice3.cli.cli_common import USBMUX_OPTION_HELP, print_json
from pymobiledevice3.lockdown import LockdownClient
from pymobiledevice3.lockdown import create_using_usbmux


@dataclass
class GlobalConfig:
    udid: str | None
    usb: bool | None
    network: bool | None
    usbmux_address: str | None

    def get_lockdown_client(self) -> LockdownClient:
        connection_type = None
        if self.usb:
            connection_type = 'USB'
        elif self.network:
            connection_type = 'Network'
        return create_using_usbmux(serial=self.udid,
                                   usbmux_address=self.usbmux_address,
                                   connection_type=connection_type)


gcfg: GlobalConfig = GlobalConfig(None, None, None, None)


def get_udid() -> str:
    if gcfg.udid:
        return gcfg.udid
    raise RuntimeError('udid not set')


# @click.option('--color/--no-color', default=True)
@click.group()
@click.option('-u', '--udid', default=None, help='udid of device')
@click.option('-u', '--usb', is_flag=True, help='show only usb devices')
@click.option('-n', '--network', is_flag=True, help='show only network devices')
@click.option('usbmux_address', '--usbmux', help=USBMUX_OPTION_HELP)
def cli(udid: str, usb: bool, network: bool, usbmux_address: str):
    gcfg.udid = udid
    gcfg.usb = usb
    gcfg.network = network
    gcfg.usbmux_address = usbmux_address
    