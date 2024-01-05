#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Fri Jan 05 2024 23:09:36 by codeskyblue
"""

from __future__ import annotations
import re

__all__ = ["download_file", "is_hyperlink", "DownloadError"]

import base64
import hashlib
import logging
import os
import pathlib
import shutil
import time
from typing import Optional, Union

import requests
from requests.structures import CaseInsensitiveDict

from tidevice3.exceptions import DownloadError

logger = logging.getLogger(__name__)

CACHE_DOWNLOAD_SUFFIX = ".t3-download-cache"
DEFAULT_DOWNLOAD_TIMEOUT = 600  # 10 minutes

StrOrPathLike = Union[str, pathlib.Path]


def md5sum(filepath: StrOrPathLike) -> str:
    """return md5sum of given file"""
    m = hashlib.md5()
    with open(filepath, "rb") as f:
        while True:
            data = f.read(1<<20)
            if not data:
                break
            m.update(data)
    return m.hexdigest()


class RemoteFileInfo:
    content_md5: str | None = None
    content_length: int = 0
    accept_ranges: bool = False


def get_remote_file_info(headers: CaseInsensitiveDict) -> RemoteFileInfo:
    """
    Get remote file info, such as content-length, content-md5, accept-ranges
    """
    info = RemoteFileInfo()
    info.content_length = int(headers.get("content-length", 0))
    info.accept_ranges = headers.get("accept-ranges") == "bytes"
    md5_base64 = headers.get("content-md5")
    if md5_base64:
        try:
            content_md5 = base64.b64decode(md5_base64).hex()
            if len(content_md5) == 32:
                info.content_md5 = content_md5
        except:
            pass
    return info


def check_if_already_downloaded(
    filepath: pathlib.Path, remote_file_info: RemoteFileInfo
) -> bool:
    if not filepath.exists():
        return False
    if filepath.stat().st_size != remote_file_info.content_length:
        return False
    if remote_file_info.content_md5:
        if md5sum(filepath) != remote_file_info.content_md5:
            return False
    return True


def update_file_mtime(filepath: pathlib.Path):
    """update file mtime to avoid flie being deleted by clean script"""
    _atime, _mtime = (time.time(), time.time())
    os.utime(filepath, (_atime, _mtime))


def download_file_from_range(
    url: str, filepath: pathlib.Path, bytes_start: int, timeout: float
):
    r = make_request_get_stream(
        url, timeout, headers={"Range": f"bytes={bytes_start}-"}
    )
    with filepath.open("ab") as f:
        shutil.copyfileobj(r.raw, f)


def get_bytes_start(
    tmpfpath: pathlib.Path, remote_file_info: RemoteFileInfo
) -> Optional[int]:
    if (
        remote_file_info.accept_ranges
        and tmpfpath.exists()
        and tmpfpath.stat().st_mtime > time.time() - 60
    ):
        return tmpfpath.stat().st_size


def make_request_get_stream(
    url: str, timeout: float, headers: dict = None
) -> requests.Response:
    r = requests.get(url, stream=True, timeout=timeout, headers=headers)
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise DownloadError(e, url)
    return r


def is_hyperlink(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")


def guess_filename_from_url(url: str, headers: CaseInsensitiveDict = {}) -> str:
    """
    Guess filename from url and headers
    """
    filename = url.split("/")[-1]
    filename = re.sub(r"\?.*$", "", filename)
    if "content-disposition" in headers:
        for part in headers["content-disposition"].split(";"):
            if part.strip().startswith("filename="):
                filename = part.split("=")[-1].strip('"')
    return filename


def download_file(
    url: str, filepath: StrOrPathLike | None = None, timeout: float = DEFAULT_DOWNLOAD_TIMEOUT
) -> pathlib.Path:
    """
    Download file from given url to filepath

    :param url: url to download
    :param filepath: local file path
    :param timeout: timeout in seconds

    raise DownloadError if download failed
    """
    if not is_hyperlink(url):
        raise DownloadError("only support http/https url", url)
    
    logger.info("download from url: %s", url)
    r = make_request_get_stream(url, timeout)

    if filepath is None:
        filepath = guess_filename_from_url(url, r.headers)
    filepath = pathlib.Path(filepath)
    tmpfpath = pathlib.Path(
        str(filepath) + CACHE_DOWNLOAD_SUFFIX
    )  # 文件先下载到这里，等检查完后再Move过去

    remote_file_info = get_remote_file_info(r.headers)
    if check_if_already_downloaded(filepath, remote_file_info):
        logger.debug("use cached asset: %s", filepath)
        update_file_mtime(filepath)
        return filepath

    bytes_start = get_bytes_start(tmpfpath, remote_file_info)
    if bytes_start:
        logger.debug("resume download from %s", bytes_start)
        download_file_from_range(url, tmpfpath, bytes_start, timeout)
    else:
        with tmpfpath.open("wb") as f:
            shutil.copyfileobj(r.raw, f)
    if not check_if_already_downloaded(tmpfpath, remote_file_info):
        tmpfpath.unlink(missing_ok=True)
        raise DownloadError("download file not complete", url)
    os.rename(tmpfpath, filepath)
    return filepath
