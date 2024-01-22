#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Fri Jan 05 2024 18:10:32 by codeskyblue
"""
from __future__ import annotations

import collections
from functools import update_wrapper

import click
from pymobiledevice3.cli.cli_common import USBMUX_OPTION_HELP

from tidevice3.api import connect_service_provider


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
@click.pass_context
def cli(ctx: click.Context, udid: str, usbmux_address: str):
    ctx.ensure_object(dict)
    ctx.obj['udid'] = udid
    ctx.obj['usbmux_address'] = usbmux_address


def pass_service_provider(func):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        udid = ctx.obj['udid']
        usbmux_address = ctx.obj['usbmux_address']
        service_provider = connect_service_provider(udid, force_usbmux=True, usbmux_address=usbmux_address)
        with service_provider:
            return ctx.invoke(func, service_provider, *args, **kwargs)
    return update_wrapper(new_func, func)


def pass_rsd(func):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        udid = ctx.obj['udid']
        usbmux_address = ctx.obj['usbmux_address']
        service_provider = connect_service_provider(udid=udid, usbmux_address=usbmux_address)
        with service_provider:
            return ctx.invoke(func, service_provider, *args, **kwargs)
    return update_wrapper(new_func, func)


CLI_GROUPS = ["list", "developer", "screenshot", "screenrecord", "fsync", "app", "reboot", "tunneld", "exec"]
for group in CLI_GROUPS:
    __import__(f"tidevice3.cli.{group}")
