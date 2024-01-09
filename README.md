# tidevice3
[![PyPI version](https://badge.fury.io/py/tidevice3.svg)](https://badge.fury.io/py/tidevice3)
[![codecov](https://codecov.io/gh/codeskyblue/tidevice3/graph/badge.svg?token=twFRe9igek)](https://codecov.io/gh/codeskyblue/tidevice3)

wrapper for pymobiledevice3 to make it more easy to use.


# Install

```bash
pip install tidevice3

# or install as Isolated environment
brew install pipx
pipx install tidevice3
```

# Usage
```bash
$ t3 list
...

# enable developer mode and mount develoepr image
$ t3 developer

# install & uninstall
$ t3 install https://....ipa
$ t3 install ./some.ipa
$ t3 uninstall com.example

# start tunneld for iOS>=17
# launch process (pmd3 remote start-tunnel) when new usb device connected
# root required
$ sudo t3 tunneld

# take screenshot
$ t3 screenshot out.png

# reboot
$ t3 reboot

# file operation
$ t3 fsync <ls|rm|pull|push> [Arguments...]

# show help
$ t3 --help
```

# DEVELOP & CONTRIBUTE
see [DEVELOP.md](DEVELOP.md)

# LICENSE
[MIT](LICENSE)