#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: ngc_container
short_description: Manage NGC container image entries
version_added: "1.0.0"
description:
    - Creates or deletes container image registry entries in the
      NVIDIA NGC Catalog via the REST API.
    - This module manages the container metadata entry, not the
      container image layers themselves.
author:
    - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
    - stevefulme1.gpu_ai_factory.ngc
options:
    name:
        description:
            - Name of the container image.
        type: str
        required: true
    display_name:
        description:
            - Human-readable display name for the container.
        type: str
    description:
        description:
            - Description of the container image.
        type: str
    state:
        description:
            - Desired state of the container entry.
        type: str
        default: present
        choices:
            - present
            - absent
requirements:
    - requests
"""

EXAMPLES = r"""
- name: Register a container image in NGC
  stevefulme1.gpu_ai_factory.ngc_container:
    ngc_api_key: "{{ vault_ngc_key }}"
    org: my-org
    name: custom-triton
    display_name: "Custom Triton Server"
    description: "Triton with custom backends"

- name: Remove a container entry
  stevefulme1.gpu_ai_factory.ngc_container:
    ngc_api_key: "{{ vault_ngc_key }}"
    org: my-org
    name: custom-triton
    state: absent
"""

RETURN = r"""
container:
    description: Container details after the operation.
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

    # Check if container exists
    existing = None
    try:
        data = client.get_container(p["org"], p["name"])
        existing = data.get("container", data)
    except Exception:
        pass

    if p["state"] == "absent":
        if existing is None:
            module.exit_json(changed=False, msg="Container does not exist")
        if module.check_mode:
            module.exit_json(changed=True, msg="Would delete container")
        try:
            client.delete("/org/{0}/containers/{1}".format(p["org"], p["name"]))
        except Exception as exc:
            module.fail_json(msg="Failed to delete container: {0}".format(exc))
        module.exit_json(changed=True, msg="Container deleted")

    # state == present
    payload = {"name": p["name"]}
    if p["display_name"]:
        payload["displayName"] = p["display_name"]
    if p["description"]:
        payload["description"] = p["description"]

    if existing:
        if module.check_mode:
            module.exit_json(changed=False, container=existing)
        try:
            data = client.put(
                "/org/{0}/containers/{1}".format(p["org"], p["name"]),
                payload=payload,
            )
        except Exception as exc:
            module.fail_json(msg="Failed to update container: {0}".format(exc))
        module.exit_json(changed=True, container=data.get("container", data))
    else:
        if module.check_mode:
            module.exit_json(changed=True, msg="Would create container")
        try:
            data = client.post(
                "/org/{0}/containers".format(p["org"]),
                payload=payload,
            )
        except Exception as exc:
            module.fail_json(msg="Failed to create container: {0}".format(exc))
        module.exit_json(changed=True, container=data.get("container", data))


if __name__ == "__main__":
    main()
