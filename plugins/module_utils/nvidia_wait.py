# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Retry and wait helpers for NVIDIA AI Factory modules."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import time

try:
    from requests.exceptions import HTTPError
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def call_with_retry(fn, *args, max_retries=3, backoff=1.0, **kwargs):
    """Call a function with retry logic for transient HTTP errors.

    Retries on 5xx server errors. Does not retry on 4xx client errors.

    Args:
        fn: The callable to invoke.
        *args: Positional arguments forwarded to *fn*.
        max_retries: Maximum number of retries (default 3).
        backoff: Base delay between retries in seconds (default 1.0).
        **kwargs: Keyword arguments forwarded to *fn*.

    Returns:
        The return value of *fn*.

    Raises:
        requests.exceptions.HTTPError: When retries are exhausted or
            the error is a non-retryable client error.
    """
    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            if HAS_REQUESTS and isinstance(exc, HTTPError):
                status = getattr(exc.response, "status_code", None)
                if status is not None and status < 500:
                    raise
            last_exc = exc
            if attempt < max_retries:
                time.sleep(backoff * (2 ** attempt))
    raise last_exc
