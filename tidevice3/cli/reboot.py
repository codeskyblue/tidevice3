#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Tue Jan 09 2024 19:09:47 by codeskyblue
"""

from __future__ import annotations

from pymobiledevice3.lockdown import LockdownClient
from pymobiledevice3.services.diagnostics import DiagnosticsService

from tidevice3.cli.cli_common import cli, pass_service_provider


@cli.command()
@pass_service_provider
def reboot(service_provider: LockdownClient):
    """reboot device"""
    with DiagnosticsService(service_provider) as diagnostics:
        diagnostics.restart()