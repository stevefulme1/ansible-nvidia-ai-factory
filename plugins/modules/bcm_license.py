#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: bcm_license
short_description: Manage BCM licenses
version_added: "1.0.0"
description:
  - Manage licenses in NVIDIA Base Command Manager.
  - Supports adding, updating, and removing BCM license keys.
  - BCM licenses control access to cluster management features,
    node count limits, and GPU management capabilities.
  - Supports check mode for safe plan/preview operations.
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - A friendly name for the license entry.
    type: str
    required: true
  state:
    description:
      - The desired state of the license.
    type: str
    choices:
      - present
      - absent
    default: present
  license_key:
    description:
      - The BCM license key string.
      - Required when I(state=present) and the license does not exist.
    type: str
  license_file:
    description:
      - Path to a license file on the controller.
      - Alternative to providing I(license_key) directly.
    type: path
  description:
    description:
      - A human-readable description of the license purpose.
    type: str
  license_type:
    description:
      - The type of license being managed.
    type: str
    choices:
      - base
      - gpu
      - enterprise
      - evaluation
    default: base
extends_documentation_fragment:
  - stevefulme1.nvidia_ai_factory.nvidia
"""

EXAMPLES = r"""
- name: Add a BCM enterprise license
  stevefulme1.nvidia_ai_factory.bcm_license:
    bcm_url: https://bcm.example.com
    bcm_token: "{{ bcm_token }}"
    name: enterprise-2026
    license_key: "{{ vault_bcm_license_key }}"
    license_type: enterprise
    description: "Enterprise license valid through 2026-12-31"
    state: present

- name: Add a license from a file
  stevefulme1.nvidia_ai_factory.bcm_license:
    bcm_url: https://bcm.example.com
    bcm_token: "{{ bcm_token }}"
    name: gpu-license
    license_file: /opt/licenses/bcm-gpu.lic
    license_type: gpu
    state: present

- name: Remove an expired license
  stevefulme1.nvidia_ai_factory.bcm_license:
    bcm_url: https://bcm.example.com
    bcm_token: "{{ bcm_token }}"
    name: old-eval-license
    state: absent
"""

RETURN = r"""
license:
  description: The license details after the operation.
  returned: success and state is present
  type: dict
  contains:
    name:
      description: The license friendly name.
      type: str
    id:
      description: The unique license identifier.
      type: str
    license_type:
      description: The license type.
      type: str
    status:
      description: The license status (active, expired, etc.).
      type: str
    expiry_date:
      description: The license expiration date.
      type: str
    node_limit:
      description: Maximum number of managed nodes.
      type: int
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.stevefulme1.nvidia_ai_factory.plugins.module_utils.nvidia_common import (
    NVIDIA_COMMON_ARGS,
    to_dict,
)
from ansible_collections.stevefulme1.nvidia_ai_factory.plugins.module_utils.nvidia_auth import (
    create_bcm_client,
)


def get_license(session, bcm_url, name):
    """Get a license by name."""
    try:
        resp = session.get(
            "{0}/api/v1/licenses".format(bcm_url),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        licenses = data if isinstance(data, list) else data.get("data", [])
        for lic in licenses:
            if lic.get("name") == name:
                return lic
    except Exception:
        pass
    return None


def main():
    argument_spec = dict(
        name=dict(type="str", required=True),
        state=dict(type="str", default="present", choices=["present", "absent"]),
        license_key=dict(type="str", no_log=True),
        license_file=dict(type="path"),
        description=dict(type="str"),
        license_type=dict(
            type="str",
            default="base",
            choices=["base", "gpu", "enterprise", "evaluation"],
        ),
    )
    argument_spec.update(NVIDIA_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ("license_key", "license_file"),
        ],
    )

    session = create_bcm_client(module)
    bcm_url = module.params["bcm_url"].rstrip("/")
    name = module.params["name"]
    state = module.params["state"]

    existing = get_license(session, bcm_url, name)

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        lic_id = existing.get("id", existing.get("name"))
        try:
            session.delete(
                "{0}/api/v1/licenses/{1}".format(bcm_url, lic_id),
                timeout=30,
            )
        except Exception as exc:
            module.fail_json(msg="Failed to delete license: {0}".format(exc))
        module.exit_json(changed=True)

    # state == present
    license_key = module.params.get("license_key")
    license_file = module.params.get("license_file")

    if not existing and not license_key and not license_file:
        module.fail_json(
            msg="license_key or license_file is required when creating a new license."
        )

    # Read license from file if specified
    if license_file:
        try:
            with open(license_file, "r") as fh:
                license_key = fh.read().strip()
        except IOError as exc:
            module.fail_json(
                msg="Failed to read license file {0}: {1}".format(
                    license_file, exc
                )
            )

    payload = {
        "name": name,
        "license_type": module.params["license_type"],
    }
    if license_key:
        payload["license_key"] = license_key
    if module.params.get("description"):
        payload["description"] = module.params["description"]

    if existing is None:
        if module.check_mode:
            safe_payload = {k: v for k, v in payload.items() if k != "license_key"}
            module.exit_json(changed=True, license=safe_payload)
        try:
            resp = session.post(
                "{0}/api/v1/licenses".format(bcm_url),
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            result = resp.json()
        except Exception as exc:
            module.fail_json(msg="Failed to add license: {0}".format(exc))
        module.exit_json(changed=True, license=to_dict(result))
    else:
        changed = False
        for key in ("license_type", "description"):
            if payload.get(key) and existing.get(key) != payload[key]:
                changed = True
                break
        if license_key:
            changed = True  # Always update if a new key is provided

        if not changed:
            module.exit_json(changed=False, license=to_dict(existing))
        if module.check_mode:
            module.exit_json(changed=True)
        lic_id = existing.get("id", existing.get("name"))
        try:
            resp = session.put(
                "{0}/api/v1/licenses/{1}".format(bcm_url, lic_id),
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            result = resp.json()
        except Exception as exc:
            module.fail_json(msg="Failed to update license: {0}".format(exc))
        module.exit_json(changed=True, license=to_dict(result))


if __name__ == "__main__":
    main()
