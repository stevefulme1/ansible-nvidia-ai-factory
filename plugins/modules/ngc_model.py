#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: ngc_model
short_description: Manage NGC model registry entries
version_added: "1.0.0"
description:
    - Creates or deletes model registry entries in the NVIDIA NGC
      Catalog via the REST API.
    - This module manages the model metadata entry, not the model
      weights themselves.
author:
    - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
    - stevefulme1.gpu_ai_factory.ngc
options:
    name:
        description:
            - Name of the model.
        type: str
        required: true
    display_name:
        description:
            - Human-readable display name for the model.
        type: str
    description:
        description:
            - Description of the model.
        type: str
    precision:
        description:
            - Model precision format.
        type: str
        choices:
            - fp32
            - fp16
            - bf16
            - int8
            - int4
    state:
        description:
            - Desired state of the model entry.
        type: str
        default: present
        choices:
            - present
            - absent
requirements:
    - requests
"""

EXAMPLES = r"""
- name: Register a model in NGC
  stevefulme1.gpu_ai_factory.ngc_model:
    ngc_api_key: "{{ vault_ngc_key }}"
    org: my-org
    name: custom-llm-v1
    display_name: "Custom LLM v1"
    description: "Fine-tuned LLM for internal use"
    precision: bf16

- name: Remove a model from NGC
  stevefulme1.gpu_ai_factory.ngc_model:
    ngc_api_key: "{{ vault_ngc_key }}"
    org: my-org
    name: custom-llm-v1
    state: absent
"""

RETURN = r"""
model:
    description: Model details after the operation.
    type: dict
    returned: when state is present
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
        name=dict(type="str", required=True),
        display_name=dict(type="str"),
        description=dict(type="str"),
        precision=dict(type="str", choices=["fp32", "fp16", "bf16", "int8", "int4"]),
        state=dict(type="str", default="present", choices=["present", "absent"]),
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

    # Check if model exists
    existing = None
    try:
        data = client.get_model(p["org"], p["name"])
        existing = data.get("model", data)
    except Exception:
        pass

    if p["state"] == "absent":
        if existing is None:
            module.exit_json(changed=False, msg="Model does not exist")
        if module.check_mode:
            module.exit_json(changed=True, msg="Would delete model")
        try:
            client.delete("/org/{0}/models/{1}".format(p["org"], p["name"]))
        except Exception as exc:
            module.fail_json(msg="Failed to delete model: {0}".format(exc))
        module.exit_json(changed=True, msg="Model deleted")

    # state == present
    payload = {"name": p["name"]}
    if p["display_name"]:
        payload["displayName"] = p["display_name"]
    if p["description"]:
        payload["description"] = p["description"]
    if p["precision"]:
        payload["precision"] = p["precision"]

    if existing:
        # Model already exists
        if module.check_mode:
            module.exit_json(changed=False, model=existing)
        try:
            data = client.put(
                "/org/{0}/models/{1}".format(p["org"], p["name"]),
                payload=payload,
            )
        except Exception as exc:
            module.fail_json(msg="Failed to update model: {0}".format(exc))
        module.exit_json(changed=True, model=data.get("model", data))
    else:
        if module.check_mode:
            module.exit_json(changed=True, msg="Would create model")
        try:
            data = client.post(
                "/org/{0}/models".format(p["org"]),
                payload=payload,
            )
        except Exception as exc:
            module.fail_json(msg="Failed to create model: {0}".format(exc))
        module.exit_json(changed=True, model=data.get("model", data))


if __name__ == "__main__":
    main()
