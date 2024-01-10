#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Fri Jan 05 2024 18:10:01 by codeskyblue
"""
import logging

from packaging.version import Version
from pymobiledevice3.exceptions import AlreadyMountedError
from pymobiledevice3.services.amfi import AmfiService
from pymobiledevice3.services.mobile_image_mounter import auto_mount

from tidevice3.cli.cli_common import cli, gcfg

logger = logging.getLogger(__name__)


@cli.command()
def developer():
    """ enable developer mode """
    service_provider = gcfg.get_lockdown_client()
    
    if Version(service_provider.product_version) >= Version("17"):
        if not service_provider.developer_mode_status:
            logger.info('enable developer mode')
            AmfiService(service_provider).enable_developer_mode()
        else:
            logger.info('developer mode already enabled')
    
    try:
        auto_mount(service_provider)
        logger.info('mount developer image')
    except AlreadyMountedError:
        logger.info('developer image already mounted')
    