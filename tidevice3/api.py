
from __future__ import annotations

import datetime
import io
import logging
import os
import socket
from typing import Any, Dict, Iterator, Optional

import requests
from packaging.version import Version
from PIL import Image
from pydantic import BaseModel
from pymobiledevice3.common import get_home_folder
from pymobiledevice3.exceptions import AlreadyMountedError
from pymobiledevice3.lockdown import LockdownClient, create_using_usbmux, usbmux
from pymobiledevice3.lockdown_service_provider import LockdownServiceProvider
from pymobiledevice3.remote.remote_service_discovery import RemoteServiceDiscoveryService
from pymobiledevice3.services.amfi import AmfiService
from pymobiledevice3.services.dvt.dvt_secure_socket_proxy import DvtSecureSocketProxyService
from pymobiledevice3.services.dvt.instruments.device_info import DeviceInfo
from pymobiledevice3.services.dvt.instruments.screenshot import Screenshot
from pymobiledevice3.services.installation_proxy import InstallationProxyService
from pymobiledevice3.services.mobile_image_mounter import auto_mount
from pymobiledevice3.services.screenshot import ScreenshotService
from pymobiledevice3.utils import get_asyncio_loop

from tidevice3.exceptions import FatalError
from tidevice3.utils.download import download_file, is_hyperlink

logger = logging.getLogger(__name__)

class DeviceShortInfo(BaseModel):
    BuildVersion: str
    ConnectionType: Optional[str]
    DeviceClass: str
    DeviceName: str
    Identifier: str
    ProductType: str
    ProductVersion: str


class ProcessInfo(BaseModel):
    isApplication: bool
    pid: int
    name: str
    realAppName: str
    startDate: datetime.datetime
    bundleIdentifier: Optional[str] = None
    foregroundRunning: Optional[bool] = None


def list_devices(
    usb: bool = True, network: bool = False, usbmux_address: Optional[str] = None
) -> list[DeviceShortInfo]:
    connected_devices = []
    for device in usbmux.list_devices(usbmux_address=usbmux_address):
        udid = device.serial

        if usb and not device.is_usb:
            continue

        if network and not device.is_network:
            continue

        lockdown = create_using_usbmux(
            udid,
            autopair=False,
            connection_type=device.connection_type,
            usbmux_address=usbmux_address,
        )
        info = DeviceShortInfo.model_validate(lockdown.short_info)
        connected_devices.append(info)
    return connected_devices


DEFAULT_TIMEOUT = 60

def connect_service_provider(udid: Optional[str], force_usbmux: bool = False, usbmux_address: Optional[str] = None) -> LockdownServiceProvider:
    """Connect to device and return LockdownServiceProvider"""
    lockdown = create_using_usbmux(serial=udid, usbmux_address=usbmux_address)
    if force_usbmux:
        return lockdown
    if lockdown.product_version >= "17":
        return connect_remote_service_discovery_service(lockdown.udid)
    return lockdown


class EnterableRemoteServiceDiscoveryService(RemoteServiceDiscoveryService):
    def __enter__(self) -> EnterableRemoteServiceDiscoveryService:
        get_asyncio_loop().run_until_complete(self.connect())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        get_asyncio_loop().run_until_complete(self.close())


def is_port_open(ip: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((ip, port)) == 0


def connect_remote_service_discovery_service(udid: str, tunneld_url: str = None) -> EnterableRemoteServiceDiscoveryService:
    if tunneld_url is None:
        if is_port_open("localhost", 49151):
            tunneld_url = "http://localhost:49151"
        else:
            tunneld_url = "http://localhost:5555" # for backward compatibility

    try:
        resp = requests.get(tunneld_url, timeout=DEFAULT_TIMEOUT)
        tunnels: Dict[str, Any] = resp.json()
        ipv6_address = tunnels.get(udid)
        if ipv6_address is None:
            raise FatalError("tunneld not ready for device", udid)
        rsd = EnterableRemoteServiceDiscoveryService(ipv6_address)
        return rsd
    except requests.RequestException:
        raise FatalError("Please run `sudo t3 tunneld` first")
    except (TimeoutError, ConnectionError):
        raise FatalError("RemoteServiceDiscoveryService connect failed")

def iter_screenshot(service_provider: LockdownClient) -> Iterator[bytes]:
    if int(service_provider.product_version.split(".")[0]) >= 17:
        with DvtSecureSocketProxyService(lockdown=service_provider) as dvt:
            screenshot_service = Screenshot(dvt)
            while True:
                yield screenshot_service.get_screenshot()
    else:
        screenshot_service = ScreenshotService(service_provider)
        while True:
            yield screenshot_service.take_screenshot()


def screenshot_png(service_provider: LockdownClient) -> bytes:
    """ get screenshot as png data """
    it = iter_screenshot(service_provider)
    png_data = next(it)
    it.close()
    return png_data


def screenshot(service_provider: LockdownClient) -> Image.Image:
    """ get screenshot as PIL.Image.Image """
    png_data = screenshot_png(service_provider)
    return Image.open(io.BytesIO(png_data)).convert("RGB")


def proclist(service_provider: LockdownClient) -> Iterator[ProcessInfo]:
    """ list running processes"""
    with DvtSecureSocketProxyService(lockdown=service_provider) as dvt:
        processes = DeviceInfo(dvt).proclist()
        for process in processes:
            if 'startDate' in process:
                process['startDate'] = str(process['startDate'])
                yield ProcessInfo.model_validate(process)


def app_install(service_provider: LockdownClient, path_or_url: str):
    if is_hyperlink(path_or_url):
        ipa_path = download_file(path_or_url)
    elif os.path.isfile(path_or_url):
        ipa_path = path_or_url
    else:
        raise ValueError("local file not found", path_or_url)
    InstallationProxyService(lockdown=service_provider).install_from_local(ipa_path)


def enable_developer_mode(service_provider: LockdownClient):
    """ enable developer mode """
    if Version(service_provider.product_version) >= Version("16"):
        if not service_provider.developer_mode_status:
            logger.info('enable developer mode')
            AmfiService(service_provider).enable_developer_mode()
        else:
            logger.info('developer mode already enabled')
    
    try:
        xcode = get_home_folder() / 'Xcode.app'
        xcode.mkdir(parents=True, exist_ok=True)
        auto_mount(service_provider, xcode=xcode)
        logger.info('mount developer image')
    except AlreadyMountedError:
        logger.info('developer image already mounted')
        