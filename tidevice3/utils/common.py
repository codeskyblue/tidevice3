#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Tue Jan 09 2024 16:56:42 by codeskyblue
"""

import functools
import threading


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