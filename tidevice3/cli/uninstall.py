#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Fri Jan 05 2024 20:03:54 by codeskyblue
"""

import logging

import click
from pymobiledevice3.services.installation_proxy import InstallationProxyService

from tidevice3.cli.cli_common import cli, gcfg

logger = logging.getLogger(__name__)


@cli.command()
@click.argument('bundle_identifier')
def uninstall(bundle_identifier: str):
    """ uninstall application """
    logger.warning("deprecated, use `t3 app uninstall` instead")
    service_provider = gcfg.get_lockdown_client()
    InstallationProxyService(lockdown=service_provider).uninstall(bundle_identifier)
    