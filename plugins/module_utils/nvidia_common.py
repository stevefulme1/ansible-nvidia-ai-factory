# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Common constants and helpers for NVIDIA AI Factory modules."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

LIFECYCLE_ACTIVE = "active"
LIFECYCLE_DELETED = "deleted"
LIFECYCLE_PROVISIONING = "provisioning"
LIFECYCLE_ERROR = "error"
LIFECYCLE_STOPPING = "stopping"

WAIT_STATES = frozenset({LIFECYCLE_PROVISIONING, LIFECYCLE_STOPPING})
READY_STATES = frozenset({LIFECYCLE_ACTIVE})
DEAD_STATES = frozenset({LIFECYCLE_DELETED, LIFECYCLE_ERROR})

NVIDIA_COMMON_ARGS = dict(
    bcm_url=dict(type="str", required=False),
    bcm_username=dict(type="str", required=False),
    bcm_password=dict(type="str", required=False, no_log=True),
    bcm_token=dict(type="str", required=False, no_log=True),
    validate_certs=dict(type="bool", default=True),
    wait=dict(type="bool", default=True),
    wait_timeout=dict(type="int", default=600),
)


def to_dict(obj):
    """Convert an API response object to a plain dict.

    Args:
        obj: The object to convert. If None, returns empty dict.
             If already a dict or list, returns as-is.

    Returns:
        A plain Python dict, list, or the original primitive value.
    """
    if obj is None:
        return {}
    return obj
