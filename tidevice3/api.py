
from __future__ import annotations

import datetime
import io
from typing import Iterator, Optional

import requests
from PIL import Image
from pydantic import BaseModel
from pymobiledevice3.lockdown import LockdownClient, create_using_usbmux, usbmux
from pymobiledevice3.lockdown_service_provider import LockdownServiceProvider
from pymobiledevice3.remote.remote_service_discovery import RemoteServiceDiscoveryService
from pymobiledevice3.services.dvt.dvt_secure_socket_proxy import DvtSecureSocketProxyService
from pymobiledevice3.services.dvt.instruments.device_info import DeviceInfo
from pymobiledevice3.services.dvt.instruments.screenshot import Screenshot
from pymobiledevice3.services.screenshot import ScreenshotService

from tidevice3.exceptions import FatalError


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


def connect_remote_service_discovery_service(udid: str, tunneld_url: str = 'http://localhost:5555') -> RemoteServiceDiscoveryService:
    try:
        resp = requests.get(tunneld_url, timeout=DEFAULT_TIMEOUT)
        tunnels = resp.json()
        ipv6_address = tunnels.get(udid)
        if ipv6_address is None:
            raise FatalError("tunneld not ready for device", udid)
        rsd = RemoteServiceDiscoveryService(ipv6_address)
        rsd.connect()
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