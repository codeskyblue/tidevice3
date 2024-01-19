#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Tue Jan 09 2024 14:05:31 by codeskyblue
"""

from __future__ import annotations

import datetime
import pathlib
import posixpath
from functools import update_wrapper
from typing import List

import click
from pydantic import BaseModel
from pymobiledevice3.exceptions import AfcException, AfcFileNotFoundError
from pymobiledevice3.lockdown import LockdownClient
from pymobiledevice3.services.afc import AfcService
from pymobiledevice3.services.house_arrest import HouseArrestService

from tidevice3.cli.cli_common import cli, pass_service_provider
from tidevice3.exceptions import FatalError


def pass_afc(func):
    @pass_service_provider
    @click.pass_context
    def new_func(ctx: click.Context, service_provider: LockdownClient, *args, **kwargs):
        if ctx.obj['bundle_id']:
            afc = HouseArrestService(lockdown=service_provider,
                                     bundle_id=ctx.obj['bundle_id'],
                                     documents_only=ctx.obj["documents"])
        else:
            afc = AfcService(lockdown=service_provider)
        
        with afc:
            try:
                return ctx.invoke(func, afc, *args, **kwargs)
            except AfcFileNotFoundError as e:
                raise FatalError(f"File not found: {e}")
    return update_wrapper(new_func, func)


@cli.group()
@click.option("-B", "--bundle-id", help="bundle id of app")
@click.option('--documents', is_flag=True)
@click.pass_context
def fsync(ctx: click.Context, bundle_id: str, documents: bool):
    """file sync"""
    ctx.ensure_object(dict)
    ctx.obj["bundle_id"] = bundle_id
    ctx.obj["documents"] = documents



@fsync.command(name="ls")
@click.argument("remote_path", required=True)
@click.option('-r', '--recursive', is_flag=True)
@pass_afc
def list(afc: AfcService, remote_path: str, recursive: bool):
    """ perform a dirlist rooted at /var/mobile/Media """
    items: List[FileInfo] = []
    for name in afc.listdir(remote_path):
        try:
            file_info = stat_file(afc, posixpath.join(remote_path, name))
            items.append(file_info)
        except AfcException as e:
            pass
    items.sort(key=lambda x: [x.is_dir(), x.mtime], reverse=True)
    for item in items:
        name = item.name + ("/" if item.is_dir() else "")
        size = byte2humansize(item.size)
        click.echo(f"{item.ifmt[2:]}\t{size}\t{name}")


@fsync.command(name="rm")
@click.argument("path", default="/")
@pass_afc
def remove(afc: AfcService, path: str):
    """ remove a file rooted at /var/mobile/Media """
    afc.rm(path)
    click.echo(path)


@fsync.command(name="push")
@click.argument('local_file', type=click.File('rb'))
@click.argument('remote_file', type=click.Path(exists=False))
@pass_afc
def afc_push(afc: AfcService, local_file, remote_file):
    """ push local file into /var/mobile/Media """
    finfo = stat_file(afc, remote_file)
    if finfo.is_dir():
        remote_file = posixpath.join(remote_file, local_file.name)
    afc.set_file_contents(remote_file, local_file.read())


@fsync.command('pull')
@click.option("-f", "--force", is_flag=True, help="force overwrite")
@click.argument('remote_file', type=click.Path(exists=False))
@click.argument('local_file', default="./", type=click.Path(exists=False, path_type=pathlib.Path))
@pass_afc
def afc_pull(afc: AfcService, remote_file, local_file: pathlib.Path, force: bool):
    """ pull remote file from /var/mobile/Media """
    if local_file.is_dir():
        local_file /= posixpath.basename(remote_file)
    
    if local_file.exists():
        if not force:
            raise click.BadParameter("local_file already exists")
    elif not local_file.parent.exists():
        raise click.BadParameter("local_file's parent not exists")
    
    finfo = stat_file(afc, remote_file)
    if finfo.is_dir():
        raise click.BadParameter("remote_file is a directory")
    local_file.write_bytes(afc.get_file_contents(remote_file))
    click.echo(f"remote:{remote_file} -> local:{local_file}")


class FileInfo(BaseModel):
    name: str
    size: int
    mtime: datetime.datetime
    ifmt: str

    def is_dir(self) -> bool:
        return self.ifmt == "S_IFDIR"


def stat2fileinfo(info: dict) -> FileInfo:
    # {'st_size': 326, 'st_blocks': 8, 'st_nlink': 1, 'st_ifmt': 'S_IFREG',
    #  'st_mtime': datetime.datetime(2023, 7, 7, 18, 55, 10, 755297),
    #  'st_birthtime': datetime.datetime(2023, 7, 7, 18, 55, 10, 754835),
    #  'st_name': 'com.apple.ibooks-sync.plist'}
    return FileInfo(
        name=info["st_name"],
        size=info["st_size"],
        ifmt=info["st_ifmt"],
        mtime=info["st_mtime"],
    )


def stat_file(afc: AfcService, path: str) -> FileInfo:
    info = afc.stat(path)
    info['st_name'] = posixpath.basename(path)
    return stat2fileinfo(info)


def byte2humansize(num_bytes):
    """
    Convert a size in bytes to a more human-readable format.

    :param num_bytes: Size in bytes.
    :return: Human-readable size.
    """
    if num_bytes < 1024.0:
        return f"{num_bytes}"
    for unit in ['K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        num_bytes /= 1024.0
        if num_bytes < 1024.0:
            return f"{num_bytes:3.1f}{unit}"
    return f"{num_bytes:.1f}Y"

