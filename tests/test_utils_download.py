#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Sat Jan 06 2024 00:04:47 by codeskyblue
"""

import base64
import hashlib
import pathlib

import pytest
from pytest_httpserver import HTTPServer

from tidevice3.exceptions import DownloadError
from tidevice3.utils.download import CACHE_DOWNLOAD_SUFFIX, download_file, guess_filename_from_url


def test_download_file(httpserver: HTTPServer, tmp_path: pathlib.Path):
    url = httpserver.url_for("/hello")
    filepath = tmp_path / 'hello.txt'
    with pytest.raises(DownloadError):
        download_file(url, filepath)
    
    httpserver.expect_oneshot_request("/hello").respond_with_data("hello12345")
    download_file(url, filepath)
    assert filepath.read_text() == 'hello12345'

    with pytest.raises(DownloadError):
        download_file("ftp://123.txt", filepath)


def test_download_file_with_range(httpserver: HTTPServer, tmp_path: pathlib.Path):
    filepath = tmp_path / 'test1.txt'
    url = httpserver.url_for("/test1")
    tmpfpath = pathlib.Path(str(filepath) + CACHE_DOWNLOAD_SUFFIX)
    tmpfpath.write_bytes(b"hixxx")
    httpserver.expect_oneshot_request("/test1") \
        .respond_with_data("test1ABCDE", 
                           headers={"Accept-Ranges": "bytes"})
    httpserver.expect_oneshot_request("/test1", headers={"Range": "bytes=5-"}) \
        .respond_with_data("ABCDE",
                           headers={"Accept-Ranges": "bytes", "Content-Range": "bytes 5-9/10"})
    download_file(httpserver.url_for("/test1"), filepath)
    assert filepath.read_text() == 'hixxxABCDE'


def test_download_with_md5(httpserver: HTTPServer, tmp_path: pathlib.Path):
    filepath = tmp_path / 'test2.txt'
    url = httpserver.url_for("/test2")
    filepath.write_bytes(b"4444")

    def hash_md5_string(data: str) -> str:
        """ return base64 md5 digest """
        m = hashlib.md5()
        m.update(data.encode())
        return base64.b64encode(m.digest()).decode()
    
    httpserver.expect_request("/test2") \
        .respond_with_data("1234", 
                           headers={"Accept-Ranges": "bytes",
                                    "Content-Md5": hash_md5_string("4444")})
    download_file(url, filepath)
    assert filepath.read_text() == '4444'
    filepath.unlink()

    # md5 not match, should raise error
    with pytest.raises(DownloadError):
        download_file(url, filepath)

    httpserver.expect_request("/test3") \
        .respond_with_data("333", 
                           headers={"Accept-Ranges": "bytes",
                                    "Content-Md5": "xxxx1122<>??"})
    url = httpserver.url_for("/test3")
    download_file(url, filepath)
    assert filepath.read_text() == '333'


def test_download_guess_filename():
    assert guess_filename_from_url("http://example.com/b/test.txt?foo=1") == "test.txt"
    