#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: bcm_software_image
short_description: Manage BCM software images
version_added: "1.0.0"
description:
  - Create, update, or delete software images in NVIDIA Base Command Manager.
  - Software images define the operating system and software stack that
    can be provisioned to DGX/HGX nodes.
  - Supports check mode for safe plan/preview operations.
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - The name of the software image.
    type: str
    required: true
  state:
    description:
      - The desired state of the software image.
    type: str
    choices:
      - present
      - absent
    default: present
  description:
    description:
      - A human-readable description of the software image.
    type: str
  base_image:
    description:
      - The base OS image to build from (e.g., C(ubuntu22.04-x86_64),
        C(rhel9-x86_64)).
    type: str
  architecture:
    description:
      - The target CPU architecture.
    type: str
    choices:
      - x86_64
      - aarch64
    default: x86_64
  kernel_version:
    description:
      - The kernel version to use in the software image.
    type: str
  packages:
    description:
      - List of additional packages to include in the image.
    type: list
    elements: str
    default: []
  kernel_modules:
    description:
      - List of kernel modules to include in the image.
    type: list
    elements: str
    default: []
  gpu_driver_version:
    description:
      - The NVIDIA GPU driver version to include.
    type: str
extends_documentation_fragment:
  - stevefulme1.nvidia_ai_factory.nvidia
"""

EXAMPLES = r"""
- name: Create a DGX software image
  stevefulme1.nvidia_ai_factory.bcm_software_image:
    bcm_url: https://bcm.example.com
    bcm_token: "{{ bcm_token }}"
    name: dgx-ubuntu22-cuda12
    base_image: ubuntu22.04-x86_64
    gpu_driver_version: "550.54.15"
    packages:
      - cuda-toolkit-12-4
      - nvidia-container-toolkit
    state: present

- name: Update an existing software image description
  stevefulme1.nvidia_ai_factory.bcm_software_image:
    bcm_url: https://bcm.example.com
    bcm_token: "{{ bcm_token }}"
    name: dgx-ubuntu22-cuda12
    description: "Production DGX image with CUDA 12.4"
    state: present

- name: Delete a software image
  stevefulme1.nvidia_ai_factory.bcm_software_image:
    bcm_url: https://bcm.example.com
    bcm_token: "{{ bcm_token }}"
    name: dgx-ubuntu22-cuda12
    state: absent
"""

RETURN = r"""
image:
  description: The software image details after the operation.
  returned: success and state is present
  type: dict
  contains:
    name:
      description: The software image name.
      type: str
    id:
      description: The unique image identifier.
      type: str
    status:
      description: The image status.
      type: str
    architecture:
      description: The CPU architecture.
      type: str
    base_image:
      description: The base OS image.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.stevefulme1.nvidia_ai_factory.plugins.module_utils.nvidia_common import (
    NVIDIA_COMMON_ARGS,
    READY_STATES,
    to_dict,
)
from ansible_collections.stevefulme1.nvidia_ai_factory.plugins.module_utils.nvidia_auth import (
    create_bcm_client,
)
from ansible_collections.stevefulme1.nvidia_ai_factory.plugins.module_utils.nvidia_wait import (
    wait_for_resource,
)


def get_image(session, bcm_url, name):
    """Get a software image by name."""
    try:
        resp = session.get(
            "{0}/api/v1/software-images".format(bcm_url),
            params={"name": name},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        images = data if isinstance(data, list) else data.get("data", [])
        for img in images:
            if img.get("name") == name:
                return img
    except Exception:
        pass
    return None


def create_image(session, bcm_url, params):
    """Create a new software image."""
    resp = session.post(
        "{0}/api/v1/software-images".format(bcm_url),
        json=params,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def update_image(session, bcm_url, image_id, params):
    """Update an existing software image."""
    resp = session.put(
        "{0}/api/v1/software-images/{1}".format(bcm_url, image_id),
        json=params,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def delete_image(session, bcm_url, image_id):
    """Delete a software image."""
    resp = session.delete(
        "{0}/api/v1/software-images/{1}".format(bcm_url, image_id),
        timeout=30,
    )
    resp.raise_for_status()


def main():
    argument_spec = dict(
        name=dict(type="str", required=True),
        state=dict(type="str", default="present", choices=["present", "absent"]),
        description=dict(type="str"),
        base_image=dict(type="str"),
        architecture=dict(type="str", default="x86_64", choices=["x86_64", "aarch64"]),
        kernel_version=dict(type="str"),
        packages=dict(type="list", elements="str", default=[]),
        kernel_modules=dict(type="list", elements="str", default=[]),
        gpu_driver_version=dict(type="str"),
    )
    argument_spec.update(NVIDIA_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("base_image",), True),
        ],
    )

    session = create_bcm_client(module)
    bcm_url = module.params["bcm_url"].rstrip("/")
    name = module.params["name"]
    state = module.params["state"]

    existing = get_image(session, bcm_url, name)

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        image_id = existing.get("id", existing.get("name"))
        delete_image(session, bcm_url, image_id)
        module.exit_json(changed=True)

    # state == present
    payload = {
        "name": name,
        "architecture": module.params["architecture"],
    }
    for key in ("description", "base_image", "kernel_version", "gpu_driver_version"):
        if module.params.get(key):
            payload[key] = module.params[key]
    if module.params["packages"]:
        payload["packages"] = module.params["packages"]
    if module.params["kernel_modules"]:
        payload["kernel_modules"] = module.params["kernel_modules"]

    if existing is None:
        if module.check_mode:
            module.exit_json(changed=True, image=payload)
        result = create_image(session, bcm_url, payload)
        module.exit_json(changed=True, image=to_dict(result))
    else:
        # Check for differences
        changed = False
        for key, value in payload.items():
            if key == "name":
                continue
            if existing.get(key) != value:
                changed = True
                break

        if not changed:
            module.exit_json(changed=False, image=to_dict(existing))
        if module.check_mode:
            module.exit_json(changed=True, image=payload)

        image_id = existing.get("id", existing.get("name"))
        result = update_image(session, bcm_url, image_id, payload)
        module.exit_json(changed=True, image=to_dict(result))


if __name__ == "__main__":
    main()
