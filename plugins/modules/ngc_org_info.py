#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: ngc_org_info
short_description: List NVIDIA NGC organizations
version_added: "1.0.0"
description:
    - Retrieves the list of organizations accessible to the
      authenticated user from the NVIDIA NGC Catalog API.
author:
    - Steve Fulmer (@stevefulme1)
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
    validate_certs:
        description:
            - Whether to validate TLS certificates.
        type: bool
        default: true
requirements:
    - requests
"""

EXAMPLES = r"""
- name: List NGC organizations
  stevefulme1.gpu_ai_factory.ngc_org_info:
    ngc_api_key: "{{ vault_ngc_key }}"
  register: orgs

- name: Show organizations
  ansible.builtin.debug:
    msg: "Org: {{ item.name }}"
  loop: "{{ orgs.organizations }}"
"""

RETURN = r"""
organizations:
    description: List of NGC organizations.
    type: list
    elements: dict
    returned: always
    contains:
        name:
            description: Organization name.
            type: str
            returned: always
        description:
            description: Organization description.
            type: str
            returned: always
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from ansible_collections.stevefulme1.gpu_ai_factory.plugins.module_utils.ngc_client import (
        NgcClient,
    )
    HAS_NGC = True
except ImportError:
    HAS_NGC = False


def main():
    argument_spec = dict(
        ngc_api_key=dict(type="str", required=True, no_log=True),
        ngc_api_base=dict(type="str", default="https://api.ngc.nvidia.com/v2"),
        validate_certs=dict(type="bool", default=True),
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_NGC:
        module.fail_json(msg="The 'requests' library is required.")

    p = module.params
    client = NgcClient(
        api_key=p["ngc_api_key"],
        api_base=p["ngc_api_base"],
        validate_certs=p["validate_certs"],
    )

    try:
        data = client.list_orgs()
    except Exception as exc:
        module.fail_json(msg="Failed to list NGC orgs: {0}".format(exc))

    orgs = data.get("organizations", data.get("orgs", []))
    if isinstance(orgs, dict):
        orgs = [orgs]

    module.exit_json(changed=False, organizations=orgs)


if __name__ == "__main__":
    main()
