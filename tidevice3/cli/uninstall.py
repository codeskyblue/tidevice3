#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Fri Jan 05 2024 20:03:54 by codeskyblue
"""

import logging

import click
from pymobiledevice3.lockdown import LockdownClient
from pymobiledevice3.services.installation_proxy import InstallationProxyService

from tidevice3.cli.cli_common import cli, pass_service_provider

logger = logging.getLogger(__name__)


@cli.command()
@click.argument('bundle_identifier')
@pass_service_provider
def uninstall(service_provider: LockdownClient, bundle_identifier: str):
    """ uninstall application """
    logger.warning("deprecated, use `t3 app uninstall` instead")
    InstallationProxyService(lockdown=service_provider).uninstall(bundle_identifier)
    