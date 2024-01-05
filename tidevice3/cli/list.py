#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Fri Jan 05 2024 18:10:01 by codeskyblue
"""
import click
from tidevice3.cli.cli_common import cli, gcfg
from pymobiledevice3.lockdown import usbmux
from pymobiledevice3 import usbmux
from pymobiledevice3.cli.cli_common import USBMUX_OPTION_HELP, print_json
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.tcp_forwarder import UsbmuxTcpForwarder


@cli.command()
@click.option('-u', '--usb', is_flag=True, help='show only usb devices')
@click.option('-n', '--network', is_flag=True, help='show only network devices')
def list(usb: bool, network: bool):
    """ list connected devices """
    connected_devices = []
    for device in usbmux.list_devices(usbmux_address=gcfg.usbmux_address):
        udid = device.serial

        if usb and not device.is_usb:
            continue

        if network and not device.is_network:
            continue

        lockdown = create_using_usbmux(udid, autopair=False, connection_type=device.connection_type,
                                       usbmux_address=gcfg.usbmux_address)
        connected_devices.append(lockdown.short_info)

    print_json(connected_devices, colored=gcfg.color)

