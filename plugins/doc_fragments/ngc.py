# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class ModuleDocFragment(object):
    """Doc fragment for NGC Catalog API modules."""

    DOCUMENTATION = r"""
options:
    ngc_api_key:
        description:
            - NVIDIA NGC API key used for Bearer token authentication.
            - Can also be set via the E(NGC_API_KEY) environment variable.
        type: str
        required: true
    ngc_api_base:
        description:
            - Base URL for the NGC API.
            - Override for testing or private NGC instances.
        type: str
        default: "https://api.ngc.nvidia.com/v2"
    org:
        description:
            - NGC organization name or ID.
        type: str
        required: true
    validate_certs:
        description:
            - Whether to validate TLS certificates.
        type: bool
        default: true
"""
