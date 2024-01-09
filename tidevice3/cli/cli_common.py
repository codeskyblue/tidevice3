#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Fri Jan 05 2024 18:10:32 by codeskyblue
"""
from __future__ import annotations
import collections

import click
from dataclasses import dataclass
from pymobiledevice3.cli.cli_common import USBMUX_OPTION_HELP
from pymobiledevice3.lockdown import LockdownClient
from pymobiledevice3.lockdown import create_using_usbmux


@dataclass
class GlobalConfig:
    udid: str | None = None
    color: bool = True
    usbmux_address: str | None = None

    def get_lockdown_client(self) -> LockdownClient:
        return create_using_usbmux(serial=self.udid, usbmux_address=self.usbmux_address)


gcfg: GlobalConfig = GlobalConfig()


def get_udid() -> str:
    if gcfg.udid:
        return gcfg.udid
    raise RuntimeError("udid not set")


class OrderedGroup(click.Group):
    def __init__(self, name=None, commands=None, *args, **attrs):
        super(OrderedGroup, self).__init__(name, commands, *args, **attrs)
        #: the registered subcommands by their exported names.
        self.commands = commands or collections.OrderedDict()

    def list_commands(self, ctx):
        return self.commands


@click.group(cls=OrderedGroup)
@click.option("-u", "--udid", default=None, help="udid of device")
@click.option("usbmux_address", "--usbmux", help=USBMUX_OPTION_HELP)
@click.option("--color/--no-color", default=True)
def cli(udid: str, usbmux_address: str, color: bool):
    gcfg.udid = udid
    gcfg.usbmux_address = usbmux_address
    gcfg.color = color


CLI_GROUPS = ["list", "developer", "install", "uninstall", "screenshot", "fsync", "reboot", "tunneld"]
for group in CLI_GROUPS:
    __import__(f"tidevice3.cli.{group}")
