# For iOS 17 auto start-tunnel

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import threading
import time
import logging
from typing import NamedTuple, Tuple

import fastapi
import uvicorn
from fastapi import FastAPI
from packaging.version import Version
from tidevice3.cli.cli_common import cli, gcfg
from tidevice3.cli.list import list_devices, DeviceShortInfo

logger = logging.getLogger(__name__)


class Address(NamedTuple):
    ip: str
    port: int


def get_connected_devices() -> list[str]:
    """ return list of udid """
    devices = list_devices(usb=True, network=False)
    # for device in usbmux.list_devices(usbmux_address=gcfg.usbmux_address):

    # usbmux = tidevice.Usbmux()
    # udids = []
    # for udid in [d.udid for d in usbmux.device_list() if d.conn_type == tidevice.ConnectionType.USB]:
    #     d = tidevice.Device(udid, usbmux)
    #     if Version(d.product_version) >= Version("17"):
    #         udids.append(udid)
    # return udids


def guess_pymobiledevice3_path() -> str:
    if shutil.which("pymobiledevice3"):
        return "pymobiledevice3"
    return ".venv/bin/pymobiledevice3"

    
def start_tunnel(udid: str) -> Tuple[Address, subprocess.Popen]:
    """
    Start program, should be killed when the main program quit
    """
    logger.info("udid: %s start-tunnel", udid)
    # cmd = ["bash", "-c", "echo ::1 1234; sleep 10001"]
    py3path = guess_pymobiledevice3_path()
    cmd = [py3path, "remote", "start-tunnel", "--script-mode", "--udid", udid]
    logger.debug("cmd: %s", (" ".join(cmd)))
    process = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output_str = process.stdout.readline().decode('utf-8').strip()
    address, port_str = output_str.split()
    port = int(port_str)
    logger.info("udid: %s tunnel address: %s", udid, [address, port])
    process.stdout = subprocess.DEVNULL # maybe not working
    return Address(address, port), process


class DeviceManager:
    def __init__(self):
        self.active_monitors = {}
        self.running = True
        self.addresses = {}

    def update_devices(self):
        current_devices = set(get_connected_devices())
        active_udids = set(self.active_monitors.keys())

        # Start monitors for new devices
        for udid in current_devices - active_udids:
            try:
                addr, process = start_tunnel(udid)
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


manager = DeviceManager()
app = FastAPI()

@app.get("/")
def get_devices():
    return manager.addresses
    

@app.get("/shutdown")
def shutdown():
    manager.shutdown()
    os.kill(os.getpid(), signal.SIGINT)
    return fastapi.Response(status_code=200, content='Server shutting down...')


def main():
    if os.getuid() != 0:
        logger.error("Please run as root")
        sys.exit(1)
    threading.Thread(target=manager.run_forever, daemon=True, name="device_manager").start()
    try:
        uvicorn.run(app, host="0.0.0.0", port=5555)
    finally:
        logger.info("Shutting down...")
        manager.shutdown()
    

if __name__ == "__main__":
    main()
