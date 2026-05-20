#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: ngc_model_info
short_description: Get model information from NVIDIA NGC
version_added: "1.0.0"
description:
    - Retrieves model information from the NVIDIA NGC Catalog API.
    - Can list all models in an organization or get details for a
      specific model by name.
author:
    - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
    - stevefulme1.gpu_ai_factory.ngc
options:
    name:
        description:
            - Name of a specific model to retrieve.
            - If omitted, all models in the organization are listed.
        type: str
requirements:
    - requests
"""

EXAMPLES = r"""
- name: List all models in an org
  stevefulme1.gpu_ai_factory.ngc_model_info:
    ngc_api_key: "{{ vault_ngc_key }}"
    org: nvidia
  register: all_models

- name: Get specific model details
  stevefulme1.gpu_ai_factory.ngc_model_info:
    ngc_api_key: "{{ vault_ngc_key }}"
    org: nvidia
    name: llama-3_1-8b-instruct
  register: model
"""

RETURN = r"""
models:
    description: List of model details (single item when O(name) is given).
    type: list
    elements: dict
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
        org=dict(type="str", required=True),
        validate_certs=dict(type="bool", default=True),
        name=dict(type="str"),
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
        if p["name"]:
            data = client.get_model(p["org"], p["name"])
            models = [data.get("model", data)]
        else:
            data = client.list_models(p["org"])
            models = data.get("models", data.get("modelList", []))
    except Exception as exc:
        module.fail_json(msg="Failed to query NGC models: {0}".format(exc))

    module.exit_json(changed=False, models=models)


if __name__ == "__main__":
    main()
