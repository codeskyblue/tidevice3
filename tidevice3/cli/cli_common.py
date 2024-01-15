#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Fri Jan 05 2024 18:10:32 by codeskyblue
"""
from __future__ import annotations
import collections

import click
from dataclasses import dataclass, field
from pymobiledevice3.cli.cli_common import USBMUX_OPTION_HELP
from pymobiledevice3.lockdown import LockdownClient
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.remote.remote_service_discovery import RemoteServiceDiscoveryService
from pymobiledevice3.lockdown_service_provider import LockdownServiceProvider
import requests

from tidevice3.exceptions import FatalError


DEFAULT_TIMEOUT = 60

@dataclass
class GlobalConfig:
    color: bool = True
    usbmux_address: str | None = None
    _udid: str | None = None
    _product_version: str | None = field(default=None, init=False)

    def _update_property(self):
        """ should be called after property changed is set """
        with self.get_lockdown_client() as lockdown_client:
            self._product_version = lockdown_client.product_version
            self._udid = lockdown_client.udid
    
    @property
    def udid(self) -> str:
        if self._udid:
            return self._udid
        self._update_property()
        return self._udid
    
    @property
    def product_version(self) -> str:
        if self._product_version:
            return self._product_version
        self._update_property()
        return self._product_version

    @property
    def major_version(self) -> int:
        return int(self.product_version.split(".")[0])
    
    def get_lockdown_client(self) -> LockdownClient:
        return create_using_usbmux(serial=self._udid, usbmux_address=self.usbmux_address)
    
    def get_service_provider(self) -> LockdownServiceProvider:
        if self.major_version >= 17:
            return self._get_remote_service_discovery_service()
        return self.get_lockdown_client()
    
    def _get_remote_service_discovery_service(self) -> RemoteServiceDiscoveryService:
        try:
            resp = requests.get("http://localhost:5555", timeout=DEFAULT_TIMEOUT)
            tunnels = resp.json()
            ipv6_address = tunnels.get(self.udid)
            if ipv6_address is None:
                raise FatalError("tunneld not ready for device", self.udid)
            rsd = RemoteServiceDiscoveryService(ipv6_address)
            rsd.connect()
            return rsd
        except requests.RequestException:
            raise FatalError("Please run `sudo t3 tunneld` first")
        except (TimeoutError, ConnectionError):
            raise FatalError("RemoteServiceDiscoveryService connect failed")


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


@click.group(cls=OrderedGroup, context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("-u", "--udid", default=None, help="udid of device")
@click.option("usbmux_address", "--usbmux", help=USBMUX_OPTION_HELP)
@click.option("--color/--no-color", default=True)
def cli(udid: str, usbmux_address: str, color: bool):
    gcfg._udid = udid
    gcfg.usbmux_address = usbmux_address
    gcfg.color = color
    

CLI_GROUPS = ["list", "developer", "install", "uninstall", "screenshot", "fsync", "app", "reboot", "tunneld", "exec"]
for group in CLI_GROUPS:
    __import__(f"tidevice3.cli.{group}")
