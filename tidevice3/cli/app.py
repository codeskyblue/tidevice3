#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Thu Jan 11 2024 14:12:29 by codeskyblue
"""


from __future__ import annotations

import logging
import os
import shlex

import click
from pymobiledevice3.cli.cli_common import print_json
from pymobiledevice3.lockdown import LockdownClient
from pymobiledevice3.services.dvt.dvt_secure_socket_proxy import DvtSecureSocketProxyService
from pymobiledevice3.services.dvt.instruments.device_info import DeviceInfo
from pymobiledevice3.services.dvt.instruments.process_control import ProcessControl
from pymobiledevice3.services.installation_proxy import InstallationProxyService

from tidevice3.api import proclist
from tidevice3.cli.cli_common import cli, pass_rsd, pass_service_provider
from tidevice3.exceptions import FatalError
from tidevice3.utils.common import print_dict_as_table
from tidevice3.utils.download import download_file, is_hyperlink

logger = logging.getLogger(__name__)

@cli.group()
def app():
    """app related commands"""
    pass


@app.command("install")
@click.argument("path_or_url")
@pass_service_provider
def app_install(service_provider: LockdownClient, path_or_url: str):
    """install given .ipa or url"""
    if is_hyperlink(path_or_url):
        ipa_path = download_file(path_or_url)
    elif os.path.isfile(path_or_url):
        ipa_path = path_or_url
    else:
        raise ValueError("local file not found", path_or_url)
    InstallationProxyService(lockdown=service_provider).install_from_local(ipa_path)


@app.command("list")
@click.option('app_type', '-t', '--type', type=click.Choice(['System', 'User', 'Hidden', 'Any']), default='Any',
              help='include only applications of given type')
@click.option("--calculate-sizes/--no-calculate-size", default=False)
@pass_service_provider
def app_list(service_provider: LockdownClient, app_type: str, calculate_sizes: bool):
    """list installed apps"""
    app_infos = InstallationProxyService(lockdown=service_provider).get_apps(app_type, calculate_sizes=calculate_sizes)
    print_dict_as_table(app_infos.values(), ["CFBundleIdentifier", "CFBundleDisplayName", "CFBundleVersion", "CFBundleShortVersionString"])


@app.command("uninstall")
@click.argument("bundle_identifier")
@pass_service_provider
def app_uninstall(service_provider: LockdownClient, bundle_identifier: str):
    """uninstall application"""
    InstallationProxyService(lockdown=service_provider).uninstall(bundle_identifier)


@app.command("launch")
@click.argument("arguments", type=click.STRING)
@click.option("--kill-existing/--no-kill-existing", default=True, help="Whether to kill an existing instance of this process")
@click.option("--suspended", is_flag=True, help="Same as WaitForDebugger")
@click.option("--env", multiple=True, type=click.Tuple((str, str)), help="Environment variables to pass to process given as a list of key value")
@click.option("--stream", is_flag=True)
@pass_rsd
def app_launch(service_provider, arguments: str, kill_existing: bool, suspended: bool, env: tuple, stream: bool):
    """launch application"""
    with DvtSecureSocketProxyService(lockdown=service_provider) as dvt:
        process_control = ProcessControl(dvt)
        parsed_arguments = shlex.split(arguments)
        pid = process_control.launch(
            bundle_id=parsed_arguments[0],
            arguments=parsed_arguments[1:],
            kill_existing=kill_existing,
            start_suspended=suspended,
            environment=dict(env),
        )
        print(f"Process launched with pid {pid}")
        while stream:
            for output_received in process_control:
                logging.getLogger(f"PID:{output_received.pid}").info(
                    output_received.message.strip()
                )


@app.command("kill")
@click.argument("pid", type=click.INT)
@pass_rsd
def app_kill(service_provider, pid: int):
    """kill application"""
    with DvtSecureSocketProxyService(lockdown=service_provider) as dvt:
        process_control = ProcessControl(dvt)
        process_control.kill(pid)


@app.command("ps")
@click.option('--json/--no-json', default=False)
@pass_rsd
def app_ps(service_provider: LockdownClient, json: bool):
    """list running processes"""
    if service_provider.product_version < "17":
        logger.warning('iOS<17 have FD leak, which will cause an error when calling round more than 250 times.')
    processes = list(proclist(service_provider))
    processes = [p.model_dump(exclude_none=True) for p in processes if p.isApplication]
    if json:
        print_json(processes)
    else:
        print_dict_as_table(processes, ["pid", "name", "bundleIdentifier", "realAppName"])


@app.command("foreground")
@pass_rsd
def app_foreground(service_provider: LockdownClient):
    """show foreground running app, requires iOS>=17"""
    if service_provider.product_version < "17":
        raise FatalError("iOS<17 not supported")
    for p in proclist(service_provider):
        if p.foregroundRunning:
            print(p.bundleIdentifier, f"pid:{p.pid}")


@app.command("info")
@click.argument("bundle_identifier")
@pass_rsd
def app_info(service_provider: LockdownClient, bundle_identifier: str):
    with InstallationProxyService(lockdown=service_provider) as iproxy:
        apps = iproxy.get_apps(bundle_identifiers=[bundle_identifier])
        print_json(apps)