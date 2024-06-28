#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Fri Jan 05 2024 18:10:32 by codeskyblue
"""
from __future__ import annotations

import collections
import logging;
from functools import update_wrapper

import click
from pymobiledevice3.cli.cli_common import USBMUX_OPTION_HELP

from tidevice3.api import connect_service_provider


logger = logging.getLogger(__name__);


class OrderedGroup(click.Group):
    def __init__(self, name=None, commands=None, *args, **attrs):
        super(OrderedGroup, self).__init__(name, commands, *args, **attrs)
        #: the registered subcommands by their exported names.
        self.commands = commands or collections.OrderedDict()

    def list_commands(self, ctx):
        return self.commands


class DeprecatedOption(click.Option): # https://stackoverflow.com/a/50402799/12857692
    def __init__(self, *args, **kwargs):
        self.deprecated = kwargs.pop("deprecated", False);
        self.preferred = kwargs.pop("preferred", None);
        super(DeprecatedOption, self).__init__(*args, **kwargs);
    # end __init__()
# end class


class CommandWithDeprecatedOptions(click.Command):
    def make_parser(self, ctx): # Hook 'make_parser()' and during processing check the name used to invoke the option to see if it is preferred
        parser = super().make_parser(ctx);

        # get the parser options
        options = set(parser._short_opt.values());
        options |= set(parser._long_opt.values());
        for option in options:
            if not isinstance(option.obj, DeprecatedOption):
                continue;
            # end if

            def make_process(an_option): # construct a closure to the parser option processor
                orig_process = an_option.process;
                opt_deprecated = getattr(an_option.obj, "deprecated", None);
                assert opt_deprecated is not None, "Expected `deprecated` value for `{}`".format(an_option.obj.name);
                opt_preferred = getattr(an_option.obj, "preferred", None);
                opt_name = getattr(an_option.obj, "name", None);

                def process(value, state): # only called if the option is set
                    if opt_deprecated:
                        vv = ["--"+opt_name];
                        msg = "The '%s' option is deprecated";
                        if opt_preferred is not None:
                            msg = msg+", use '%s' instead";
                            vv.append(opt_preferred);
                        # end if
                        logger.warning(msg % tuple(vv));
                    # end if
                    return orig_process(value, state);
                # end process()

                return process;
            # end make_process()

            option.process = make_process(option);
        # end for
        return parser;
    # end make_parser()
# end class


@click.group(cls=OrderedGroup, context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("-u", "--udid", default=None, help="udid of device")
@click.option("tunneld_port", "--tunneld-port", default=5555, help="tunneld listen port")
@click.option("usbmux_address", "--usbmux", help=USBMUX_OPTION_HELP)
@click.pass_context
def cli(ctx: click.Context, udid: str, usbmux_address: str, tunneld_port: int):
    ctx.ensure_object(dict)
    ctx.obj['udid'] = udid
    ctx.obj['usbmux_address'] = usbmux_address
    ctx.obj["tunneld_port"] = tunneld_port;


def pass_service_provider(func):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        udid = ctx.obj['udid']
        usbmux_address = ctx.obj['usbmux_address']
        service_provider = connect_service_provider(udid, force_usbmux=True, usbmux_address=usbmux_address)
        with service_provider:
            return ctx.invoke(func, service_provider, *args, **kwargs)
    return update_wrapper(new_func, func)


def pass_rsd(func):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        udid = ctx.obj['udid']
        usbmux_address = ctx.obj['usbmux_address']
        tunneld_port = ctx.obj["tunneld_port"];
        service_provider = connect_service_provider(udid=udid, usbmux_address=usbmux_address, tunneld_port=tunneld_port)
        with service_provider:
            return ctx.invoke(func, service_provider, *args, **kwargs)
    return update_wrapper(new_func, func)


CLI_GROUPS = ["list", "info", "developer", "screenshot", "screenrecord", "install", "fsync", "app", "reboot", "tunneld", "runwda", "relay", "exec"]
for group in CLI_GROUPS:
    __import__(f"tidevice3.cli.{group}")
