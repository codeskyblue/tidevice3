#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Fri Jan 05 2024 17:47:29 by codeskyblue
"""
import logging
import sys

import click
from pymobiledevice3.exceptions import NoDeviceConnectedError

from tidevice3.cli.cli_common import cli
from tidevice3.exceptions import BaseException, FatalError

logger = logging.getLogger(__name__)


def main():
    try:
        cli(auto_envvar_prefix='T3')
    except FatalError as e:
        click.echo(f"Error: {e}")
        sys.exit(1)
    except NoDeviceConnectedError:
        logger.error("No device connected")
        sys.exit(1)
    except BaseException as e:
        click.echo(f"Error: {type(e)} {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception("unhandled exception: %s", e)
        sys.exit(2)


if __name__ == '__main__':
    main()