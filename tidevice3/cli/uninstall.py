#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Fri Jan 05 2024 20:03:54 by codeskyblue
"""

import logging

import click
from tidevice3.cli.cli_common import cli, gcfg
from pymobiledevice3.services.installation_proxy import InstallationProxyService

logger = logging.getLogger(__name__)


@cli.command()
@click.argument('bundle_identifier')
def uninstall(bundle_identifier: str):
    """ uninstall application """
    service_provider = gcfg.get_lockdown_client()
    InstallationProxyService(lockdown=service_provider).uninstall(bundle_identifier)
    