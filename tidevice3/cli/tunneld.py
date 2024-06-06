# For iOS 17 auto start-tunnel

from __future__ import annotations

import logging
import os
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time
from typing import List, Mapping, NamedTuple, Tuple

import click
import fastapi
import uvicorn
from fastapi import FastAPI
from packaging.version import Version
from pymobiledevice3.exceptions import MuxException
from pymobiledevice3.osu.os_utils import OsUtils

from tidevice3.cli.cli_common import cli
from tidevice3.cli.list import list_devices
from tidevice3.utils.common import threadsafe_function

logger = logging.getLogger(__name__)
os_utils = OsUtils.create()


class Address(NamedTuple):
    ip: str
    port: int


class DeviceMiniInfo(NamedTuple):
    Udid: str
    ConnectionType: str
    ProductVersion: str


def get_connected_devices(wifi: bool) -> List[DeviceMiniInfo]:
    """return list of udid"""
    try:
        usb_devices = list_devices(usb=True, network=False)
        devices = [DeviceMiniInfo(d.Identifier, d.ConnectionType, d.ProductVersion) for d in usb_devices if Version(d.ProductVersion) >= Version("17")]
        if wifi:
            wifi_devices = list_devices(usb=False, network=True)
            devices.extend([DeviceMiniInfo(d.Identifier, d.ConnectionType, d.ProductVersion) for d in wifi_devices if Version(d.ProductVersion) >= Version("17")])
    except MuxException as e:
        logger.error("list_devices failed: %s", e)
        return []
    return devices


def guess_pymobiledevice3_cmd() -> List[str]:
    pmd3path = shutil.which("pymobiledevice3")
    if not pmd3path:
        return [sys.executable, '-m', 'pymobiledevice3']
    return [pmd3path]


class TunnelError(Exception):
    pass


@threadsafe_function
def start_tunnel(pmd3_path: List[str], device: DeviceMiniInfo) -> Tuple[Address, subprocess.Popen]:
    """
    Start program, should be killed when the main program quit

    Raises:
        TunnelError
    """
    # cmd = ["bash", "-c", "echo ::1 1234; sleep 10001"]
    log_prefix = f"[{device.Udid}]"
    start_tunnel_cmd = "remote"
    if device.ConnectionType == "Network" and Version(device.ProductVersion) < Version("17.4"):
        cmdargs = pmd3_path + f"{start_tunnel_cmd} start-tunnel --script-mode --udid {device.Udid} -t wifi".split()
    else:
        if Version(device.ProductVersion) >= Version("17.4"):
            start_tunnel_cmd = "lockdown"
        cmdargs = pmd3_path + f"{start_tunnel_cmd} start-tunnel --script-mode --udid {device.Udid}".split()
    logger.info("%s cmd: %s", log_prefix, shlex.join(cmdargs))
    process = subprocess.Popen(
        cmdargs, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE
    )
    output_str = process.stdout.readline().decode("utf-8").strip()
    if output_str == "":
        raise TunnelError("pmd3 start-tunnel empty response")
    address, port_str = output_str.split()
    port = int(port_str)
    logger.info("%s tunnel address: %s", log_prefix, [address, port])
    process.stdout = subprocess.DEVNULL  # maybe not working
    return Address(address, port), process


class DeviceManager:
    def __init__(self):
        self.active_monitors: Mapping[str, subprocess.Popen] = {}
        self.running = True
        self.addresses: Mapping[str, Address] = {}
        self.pmd3_cmd = ["pymobiledevice3"]

    def update_devices(self, wifi: bool):
        current_devices = get_connected_devices(wifi)
        current_udids = [d.Udid for d in current_devices]
        active_udids = self.active_monitors.keys()

        # Start monitors for new devices
        for device in current_devices:
            if device.Udid in active_udids:
                continue
            self.active_monitors[device.Udid] = None
            try:
                threading.Thread(name=f"{device.Udid} keeper",
                                 target=self._start_tunnel_keeper,
                                 args=(device,),
                                 daemon=True).start()
            except Exception as e:
                logger.error("udid: %s start-tunnel failed: %s", device, e)

        # Stop monitors for disconnected devices
        for udid in active_udids:
            if udid in current_udids:
                continue
            logger.info("udid: %s quit, terminate related process", udid)
            process = self.active_monitors[udid]
            if process:
                process.terminate()
            self.active_monitors.pop(udid, None)
            self.addresses.pop(udid, None)

    def _start_tunnel_keeper(self, device: DeviceMiniInfo):
        while device.Udid in self.active_monitors:
            try:
                addr, process = start_tunnel(self.pmd3_cmd, device)
                self.active_monitors[device.Udid] = process
                self.addresses[device.Udid] = addr
                self._wait_process_exit(process, device)
            except TunnelError:
                logger.exception("udid: %s start-tunnel failed", device)
            time.sleep(3)

    def _wait_process_exit(self, process: subprocess.Popen, device: DeviceMiniInfo):
        while True:
            try:
                process.wait(1.0)
                self.addresses.pop(device.Udid, None)
                logger.warning("udid: %s process exit with code: %s", device, process.returncode)
                break
            except subprocess.TimeoutExpired:
                continue

    def shutdown(self):
        logger.info("terminate all processes")
        for process in self.active_monitors.values():
            if process:
                process.terminate()
        self.running = False

    def run_forever(self, wifi: bool):
        while self.running:
            try:
                self.update_devices(wifi)
            except Exception as e:
                logger.exception("update_devices failed: %s", e)
            time.sleep(1)


@cli.command(context_settings={"show_default": True})
@click.option(
    "--pmd3-path",
    "pmd3_path",
    help="pymobiledevice3 cli path",
    default=None,
)
@click.option("--port", "port", help="listen port", default=5555)
@click.option("--wifi", is_flag=True, help="start-tunnel for network devices")
def tunneld(pmd3_path: str, port: int, wifi: bool):
    """start server for iOS >= 17 auto start-tunnel, function like pymobiledevice3 remote tunneld"""
    if not os_utils.is_admin:
        logger.error("Please run as root(Mac) or administrator(Windows)")
        sys.exit(1)

    manager = DeviceManager()
    app = FastAPI()

    @app.get("/")
    def get_devices():
        return manager.addresses

    @app.get("/shutdown")
    def shutdown():
        manager.shutdown()
        os.kill(os.getpid(), signal.SIGINT)
        return fastapi.Response(status_code=200, content="Server shutting down...")

    if pmd3_path is None:
        manager.pmd3_cmd = guess_pymobiledevice3_cmd()
    else:
        manager.pmd3_cmd = [pmd3_path]

    threading.Thread(
        target=manager.run_forever, args=(wifi,), daemon=True, name="device_manager"
    ).start()
    try:
        uvicorn.run(app, host="0.0.0.0", port=port)
    finally:
        logger.info("Shutting down...")
        manager.shutdown()
