#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Mon Jan 29 2024 14:15:52 by codeskyblue
"""


import logging
import threading
import time
import typing

import click
from pymobiledevice3.lockdown import LockdownClient
from pymobiledevice3.services.dvt.testmanaged.xcuitest import XCUITestService
from pymobiledevice3.services.installation_proxy import InstallationProxyService
from pymobiledevice3.tcp_forwarder import UsbmuxTcpForwarder

from tidevice3.cli.cli_common import cli, pass_rsd

logger = logging.getLogger(__name__)


def guess_wda_bundle_id(service_provider: LockdownClient) -> typing.Optional[str]:
    app_infos = InstallationProxyService(lockdown=service_provider).get_apps('User')
    wda_bundle_ids = []
    for bundle_id in app_infos.keys():
        if bundle_id.endswith(".xctrunner"):
            wda_bundle_ids.append(bundle_id)
    wda_bundle_ids.sort(key=lambda x: x.find('WebDriverAgentRunner'), reverse=True)
    if not wda_bundle_ids:
        return None
    return wda_bundle_ids[0]


@cli.command("runwda")
@click.option('--bundle-id', default=None, help="WebDriverAgent bundle id")
@click.option("--src-port", default=8100, help="WebDriverAgent listen port")
@click.option("--dst-port", default=8100, help="local listen port")
@pass_rsd
def cli_runwda(service_provider: LockdownClient, bundle_id: str, src_port: int, dst_port: int):
    """run WebDriverAgent"""
    if not bundle_id:
        bundle_id = guess_wda_bundle_id(service_provider)
        if not bundle_id:
            raise ValueError("WebDriverAgent not found")
    
    def tcp_forwarder():
        logger.info("forwarder started, listen on %s", dst_port)
        forwarder = UsbmuxTcpForwarder(service_provider.udid, dst_port, src_port)
        forwarder.start()
    
    def xcuitest():
        XCUITestService(service_provider).run(bundle_id)

    thread1 = threading.Thread(target=tcp_forwarder, daemon=True)
    thread2 = threading.Thread(target=xcuitest, daemon=True)
    thread1.start()
    thread2.start()

    while thread1.is_alive() and thread2.is_alive():
        time.sleep(0.1)
    logger.info("Program exited")
    