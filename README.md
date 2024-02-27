# tidevice3
[![PyPI version](https://badge.fury.io/py/tidevice3.svg)](https://badge.fury.io/py/tidevice3)
[![codecov](https://codecov.io/gh/codeskyblue/tidevice3/graph/badge.svg?token=twFRe9igek)](https://codecov.io/gh/codeskyblue/tidevice3)

wrapper for [pymobiledevice3](https://github.com/doronz88/pymobiledevice3) to make it more easy to use.


# Install

Mac

```bash
pip install tidevice3

# or install as Isolated environment
brew install pipx
pipx install tidevice3
```

Linux

```bash
# required by pytun-pmd3
sudo apt install python3-dev gcc pipx
pipx install tidevice3
pipx ensurepath
```

# CLI Usage

iOS >= 17 `screenshot,app:ps` connect through Ethernet over USB (NCM device) instead of usbmuxd
So tunneld should start first.

```bash
# start tunneld for iOS>=17
# launch process (pmd3 remote start-tunnel) when new usb device connected
# root required
$ sudo t3 tunneld
```

Basic usage

```bash
$ t3 list
...

# enable developer mode and mount develoepr image
$ t3 developer

# install & uninstall
$ t3 install https://....ipa
$ t3 install ./some.ipa
$ t3 uninstall com.example

# take screenshot
$ t3 screenshot out.png

# reboot
$ t3 reboot

# file operation
$ t3 fsync <ls|rm|pull|push> [Arguments...]

# app
$ t3 app <ps|list|launch|kill|instal|uninstall|foreground>

# install
# alias for app install
$ t3 install <URL or LocalIPA>

# screenrecord
$ t3 screenrecord out.mp4

# show help
$ t3 --help
```

# API Usage
The API alone is insufficient for all operations; combining it with the pymobiledevice3 library can accomplish more things.

```python
from tidevice3.api import list_devices, connect_service_provider, screenshot, app_install

for d in list_devices(usb=True):
    print("UDID:", d.Identifier)
    service_provider = connect_service_provider(d.Identifier)
    pil_im = screenshot(service_provider)
    pil_im.save("screenshot.png")

    # install ipa from URL or local
    app_install(service_provider, "https://example.org/some.ipa")
```

# iOS 17 support
- Mac (supported)
- Windows (https://github.com/doronz88/pymobiledevice3/issues/569)
- Linux (https://github.com/doronz88/pymobiledevice3/issues/566)

Mac,Windows,Linux all supported iOS<17

# WDA
其实WDA启动可以不用XCUITest，下面是具体的方法（适用于iOS >= 15)

- iOS企业重签名方法 https://zhuanlan.zhihu.com/p/673521212
- iOS WDA脱离xcode & tidevice运行自动化 https://zhuanlan.zhihu.com/p/673319266

# DEVELOP & CONTRIBUTE
see [DEVELOP.md](DEVELOP.md)

# LICENSE
[MIT](LICENSE)
