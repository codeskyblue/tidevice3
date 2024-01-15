#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Thu Jan 11 2024 14:12:29 by codeskyblue
"""


from __future__ import annotations

import logging
import os
import shlex

import click
from pydantic import BaseModel
from pymobiledevice3.services.afc import AfcService
from pymobiledevice3.services.installation_proxy import InstallationProxyService
from pymobiledevice3.cli.cli_common import print_json
from pymobiledevice3.services.dvt.instruments.process_control import ProcessControl
from pymobiledevice3.services.dvt.dvt_secure_socket_proxy import DvtSecureSocketProxyService
from pymobiledevice3.services.dvt.instruments.device_info import DeviceInfo

from tidevice3.cli.cli_common import cli, gcfg
from tidevice3.utils.common import print_dict_as_table
from tidevice3.utils.download import download_file, is_hyperlink


@cli.group()
def app():
    """app related commands"""
    pass


@app.command("install")
@click.argument("path_or_url")
def app_install(path_or_url: str):
    """install given .ipa"""
    if is_hyperlink(path_or_url):
        ipa_path = download_file(path_or_url)
    elif os.path.isfile(path_or_url):
        ipa_path = path_or_url
    else:
        raise ValueError("local file not found", path_or_url)
    service_provider = gcfg.get_lockdown_client()
    InstallationProxyService(lockdown=service_provider).install_from_local(ipa_path)


@app.command("list")
@click.option("-u", "--user", is_flag=True, help="include user apps")
@click.option("-s", "--system", is_flag=True, help="include system apps")
@click.option("--hidden", is_flag=True, help="include hidden apps")
@click.option("--calculate-sizes/--no-calculate-size", default=False)
def app_list(user: bool, system: bool, hidden: bool, calculate_sizes: bool):
    """list installed apps"""
    service_provider = gcfg.get_lockdown_client()
    app_types = []
    if user:
        app_types.append("User")
    if system:
        app_types.append("System")
    if hidden:
        app_types.append("Hidden")
    app_infos = InstallationProxyService(lockdown=service_provider).get_apps(
        app_types, calculate_sizes=calculate_sizes
    )
    print_dict_as_table(app_infos.values(), ["CFBundleIdentifier", "CFBundleDisplayName", "CFBundleVersion", "CFBundleShortVersionString"])


# @app.command()
# @click.argument("bundle_identifier")
# def info(bundle_identifier: str):
#     """show app info"""
#     pass


@app.command("uninstall")
@click.argument("bundle_identifier")
def app_uninstall(bundle_identifier: str):
    """uninstall application"""
    service_provider = gcfg.get_lockdown_client()
    InstallationProxyService(lockdown=service_provider).uninstall(bundle_identifier)


@app.command("launch")
@click.argument("arguments", type=click.STRING)
@click.option("--kill-existing/--no-kill-existing", default=True, help="Whether to kill an existing instance of this process")
@click.option("--suspended", is_flag=True, help="Same as WaitForDebugger")
@click.option("--env", multiple=True, type=click.Tuple((str, str)), help="Environment variables to pass to process given as a list of key value")
@click.option("--stream", is_flag=True)
def app_launch(arguments: str, kill_existing: bool, suspended: bool, env: tuple, stream: bool):
    """launch application"""
    service_provider = gcfg.get_service_provider()
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
def app_kill(pid: int):
    """kill application"""
    service_provider = gcfg.get_service_provider()
    with DvtSecureSocketProxyService(lockdown=service_provider) as dvt:
        process_control = ProcessControl(dvt)
        process_control.kill(pid)


@app.command("ps")
@click.option('--color/--no-color', default=True)
def app_ps(color: bool):
    """list running processes"""
    service_provider = gcfg.get_service_provider()
    with DvtSecureSocketProxyService(lockdown=service_provider) as dvt:
        processes = DeviceInfo(dvt).proclist()
        for process in processes:
            if 'startDate' in process:
                process['startDate'] = str(process['startDate'])
        print_json(processes, colored=color)