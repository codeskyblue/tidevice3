#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Tue Feb 27 2024 10:38:24 by codeskyblue
"""

from pymobiledevice3.cli.cli_common import print_json
from pymobiledevice3.lockdown import LockdownClient

from tidevice3.cli.cli_common import cli, pass_service_provider


@cli.command("info")
@pass_service_provider
def info(service_provider: LockdownClient):
    """ print device info """
    print_json(service_provider.short_info)

