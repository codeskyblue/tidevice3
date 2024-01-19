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


def unicode_len(s: str) -> int:
    """ printable length of string """
    length = 0
    for char in s:
        if unicodedata.east_asian_width(char) in ('F', 'W'):
            length += 2
        else:
            length += 1
    return length


def ljust(s, length: int):
    s = str(s)
    return s + ' ' * (length - unicode_len(s))


def print_dict_as_table(dict_values: list[dict], headers: list[str], sep: str = " "):
    """
    Output as format
    ----------------------------------------
    Identifier                DeviceName ProductType ProductVersion ConnectionType
    00000000-1234567890123456 MIMM       iPhone13,3  17.2           USB
    """
    header_with_lengths = []
    for header in headers:
        if dict_values:
            max_len = max([unicode_len(str(item.get(header, ""))) for item in dict_values])
        else:
            max_len = 0
        header_with_lengths.append((header, max(max_len, unicode_len(header))))
    rows = []
    # print header
    for header, _len in header_with_lengths:
        rows.append(ljust(header, _len))
    print(sep.join(rows).rstrip())
    # print rows
    for item in dict_values:
        rows = []
        for header, _len in header_with_lengths:
            rows.append(ljust(item.get(header, ""), _len))
        print(sep.join(rows).rstrip())
        