#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Mon Mar 18 2024 14:03:09 by codeskyblue

Ref: https://github.com/doronz88/pymobiledevice3/blob/master/pymobiledevice3/cli/usbmux.py#L32
"""

import logging
import tempfile
import threading
from functools import partial

import click
from pymobiledevice3.lockdown import LockdownClient
from pymobiledevice3.tcp_forwarder import UsbmuxTcpForwarder

from tidevice3.cli.cli_common import cli, pass_service_provider

logger = logging.getLogger(__name__)

@cli.command('relay')
@click.argument("local_port", type=click.IntRange(1, 0xffff))
@click.argument("device_port", type=click.IntRange(1, 0xffff))
@click.option('-s', '--source', default='127.0.0.1', help="source address for listening socket", show_default=True)
@click.option('-d', '--daemonize', is_flag=True)
@pass_service_provider
def relay(service_provider: LockdownClient, local_port: int, device_port: int, source: str, daemonize: bool):
    """Relay tcp connection from local to device"""
    listening_event = threading.Event()
    forwarder = UsbmuxTcpForwarder(service_provider.udid, device_port, local_port, listening_event=listening_event)
    logger.info("Relay from %s:%d to device:%d", source, local_port, device_port)
    if daemonize:
        try:
            from daemonize import Daemonize
        except ImportError:
            raise NotImplementedError('daemonizing is only supported on unix platforms')

        with tempfile.NamedTemporaryFile('wt') as pid_file:
            daemon = Daemonize(
                app=f'forwarder {local_port}->{device_port}',
                pid=pid_file.name,
                action=partial(forwarder.start, source),
                verbose=True)
            daemon.start()
    else:
        forwarder.start(source)