#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Tue Jan 09 2024 16:56:42 by codeskyblue
"""
from __future__ import annotations

import functools
import threading
import unicodedata


def threadsafe_function(fn):
    """
    A decorator to make thread-safe functions by using a lock.

    Args:
    fn (function): The function to be decorated.

    Returns:
    function: The decorated thread-safe function.
    """
    lock = threading.Lock()

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        with lock:
            return fn(*args, **kwargs)

    return wrapper


def display_length(s: str):
    length = 0
    for char in s:
        if unicodedata.east_asian_width(char) in ('F', 'W'):
            length += 2
        else:
            length += 1
    return length


def ljust(s, length: int):
    s = str(s)
    return s + ' ' * (length - display_length(s))


def print_dict_as_table(dict_values: list[dict], headers: list[str], sep: str = " "):
    """
    Output as format
    ----------------------------------------
    Identifier                DeviceName ProductType ProductVersion ConnectionType
    00000000-1234567890123456 MIMM       iPhone13,3  17.2           USB
    """
    header_lens = []
    for header in headers:
        if dict_values:
            max_len = max([display_length(str(item.get(header, "-"))) for item in dict_values])
        else:
            max_len = 0
        header_lens.append(max(max_len, display_length(header)))
    rows = []
    # print header
    for header, header_len in zip(headers, header_lens):
        rows.append(ljust(header, header_len))
    print(sep.join(rows).rstrip())
    # print rows
    for item in dict_values:
        rows = []
        for header, header_len in zip(headers, header_lens):
            rows.append(ljust(item.get(header, ""), header_len))
        print(sep.join(rows).rstrip())
        