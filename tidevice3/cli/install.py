#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Fri Jan 05 2024 20:03:54 by codeskyblue
"""

import logging
import os

import click
from pymobiledevice3.services.installation_proxy import \
    InstallationProxyService

from tidevice3.cli.cli_common import cli, gcfg
from tidevice3.utils.download import download_file, is_hyperlink

logger = logging.getLogger(__name__)


@cli.command()
@click.argument('path_or_url')
def install(path_or_url: str):
    """ install given .ipa """
    if is_hyperlink(path_or_url):
        ipa_path = download_file(path_or_url)
    elif os.path.isfile(path_or_url):
        ipa_path = path_or_url
    else:
        raise ValueError('local file not found', path_or_url)
    service_provider = gcfg.get_lockdown_client()
    InstallationProxyService(lockdown=service_provider).install_from_local(ipa_path)
