# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class ModuleDocFragment(object):
    """Doc fragment for DGX Redfish BMC modules."""

    DOCUMENTATION = r"""
options:
    bmc_host:
        description:
            - Hostname or IP address of the DGX BMC.
        type: str
        required: true
    bmc_username:
        description:
            - Username for BMC Basic authentication.
        type: str
        required: true
    bmc_password:
        description:
            - Password for BMC Basic authentication.
        type: str
        required: true
    validate_certs:
        description:
            - Whether to validate TLS certificates when connecting to the BMC.
        type: bool
        default: true
    system_id:
        description:
            - Redfish System ID.
            - Defaults to C(1) which is correct for single-system DGX nodes.
        type: str
        default: "1"
"""
