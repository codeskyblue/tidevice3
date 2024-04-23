import sys
from pathlib import Path

import pytest

from tidevice3.api import connect_service_provider, list_devices, screenshot


@pytest.mark.skipif(sys.platform != "darwin", reason="only run on mac")
def test_api(tmp_path: Path):
    for d in list_devices(usb=True):
        print("UDID:", d.Identifier)
        service_provider = connect_service_provider(d.Identifier)
        with service_provider:
            pil_im = screenshot(service_provider)
            pil_im.save(tmp_path / "screenshot.png")
