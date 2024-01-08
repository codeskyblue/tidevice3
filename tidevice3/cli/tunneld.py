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
from typing import Mapping, NamedTuple, Tuple
import click

import fastapi
import uvicorn
from fastapi import FastAPI
from packaging.version import Version

from tidevice3.cli.cli_common import cli
from tidevice3.cli.list import list_devices

logger = logging.getLogger(__name__)


class Address(NamedTuple):
    ip: str
    port: int


def get_connected_devices() -> list[str]:
    """return list of udid"""
    devices = list_devices(usb=True, network=False)
    return [d.Identifier for d in devices if Version(d.ProductVersion) >= Version("17")]


def guess_pymobiledevice3_path() -> str:
    if shutil.which("pymobiledevice3"):
        return "pymobiledevice3"
    return ".venv/bin/pymobiledevice3"


def start_tunnel(pmd3_path: str, udid: str) -> Tuple[Address, subprocess.Popen]:
    """
    Start program, should be killed when the main program quit
    """
    # cmd = ["bash", "-c", "echo ::1 1234; sleep 10001"]
    log_prefix = f"[{udid}]"
    cmd = f" {pmd3_path} remote start-tunnel --script-mode --udid {udid}"
    logger.info("%s cmd: %s", log_prefix, cmd)
    process = subprocess.Popen(
        shlex.split(cmd), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE
    )
    output_str = process.stdout.readline().decode("utf-8").strip()
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
        self.pmd3_path = "pymobiledevice3"

    def update_devices(self):
        current_devices = set(get_connected_devices())
        active_udids = set(self.active_monitors.keys())

        # Start monitors for new devices
        for udid in current_devices - active_udids:
            try:
                addr, process = start_tunnel(self.pmd3_path, udid)
                self.active_monitors[udid] = process
                self.addresses[udid] = addr
            except Exception as e:
                logger.error("udid: %s start-tunnel failed: %s", udid, e)
                self.active_monitors[udid] = None

        # Stop monitors for disconnected devices
        for udid in active_udids - current_devices:
            logger.info("udid: %s quit, terminate related process", udid)
            process = self.active_monitors[udid]
            if process:
                process.terminate()
            self.active_monitors.pop(udid, None)
            self.addresses.pop(udid, None)

    def shutdown(self):
        logger.info("terminate all processes")
        for process in self.active_monitors.values():
            if process:
                process.terminate()
        self.running = False

    def run_forever(self):
        while self.running:
            try:
                self.update_devices()
            except Exception as e:
                logger.exception("update_devices failed: %s", e)
            time.sleep(1)


@cli.command(context_settings={"show_default": True})
@click.option(
    "--pmd3-path",
    "pmd3_path",
    help="pymobiledevice3 cli path",
    default=guess_pymobiledevice3_path(),
)
@click.option("--port", "port", help="listen port", default=5555)
def tunneld(pmd3_path: str, port: int):
    """start server for iOS >= 17 auto start-tunnel, function like pymobiledevice3 remote tunneld"""
    if os.getuid() != 0:
        logger.error("Please run as root")
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

    manager.pmd3_path = pmd3_path

    threading.Thread(
        target=manager.run_forever, daemon=True, name="device_manager"
    ).start()
    try:
        uvicorn.run(app, host="0.0.0.0", port=port)
    finally:
        logger.info("Shutting down...")
        manager.shutdown()
