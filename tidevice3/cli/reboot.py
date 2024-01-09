#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Tue Jan 09 2024 19:09:47 by codeskyblue
"""

from __future__ import annotations

from typing import Optional

import click
from pydantic import BaseModel
from pymobiledevice3.services.diagnostics import DiagnosticsService

from tidevice3.cli.cli_common import cli, gcfg


@cli.command()
def reboot():
    """reboot device"""
    lockdown_client = gcfg.get_lockdown_client()
    with DiagnosticsService(lockdown_client) as diagnostics:
        diagnostics.restart()