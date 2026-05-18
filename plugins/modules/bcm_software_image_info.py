#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: bcm_software_image_info
short_description: List available BCM software images
version_added: "1.0.0"
description:
  - Retrieves information about software images available in NVIDIA
    Base Command Manager.
  - Can filter by name, architecture, or distribution.
  - This is an info module and always runs in check mode.
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Filter images by exact name.
      - If not specified, all images are returned.
    type: str
  architecture:
    description:
      - Filter images by CPU architecture.
    type: str
    choices:
      - x86_64
      - aarch64
  distro:
    description:
      - Filter images by distribution (e.g., C(ubuntu22.04), C(rhel9)).
    type: str
extends_documentation_fragment:
  - stevefulme1.nvidia_ai_factory.nvidia
"""

EXAMPLES = r"""
- name: List all available software images
  stevefulme1.nvidia_ai_factory.bcm_software_image_info:
    bcm_url: https://bcm.example.com
    bcm_token: "{{ bcm_token }}"
  register: all_images

- name: List x86_64 images only
  stevefulme1.nvidia_ai_factory.bcm_software_image_info:
    bcm_url: https://bcm.example.com
    bcm_token: "{{ bcm_token }}"
    architecture: x86_64
  register: x86_images

- name: Get a specific image by name
  stevefulme1.nvidia_ai_factory.bcm_software_image_info:
    bcm_url: https://bcm.example.com
    bcm_token: "{{ bcm_token }}"
    name: dgx-ubuntu22-cuda12
  register: image_detail
"""

RETURN = r"""
images:
  description: List of software images matching the filter criteria.
  returned: always
  type: list
  elements: dict
  contains:
    name:
      description: The software image name.
      type: str
    id:
      description: The unique image identifier.
      type: str
    architecture:
      description: The CPU architecture.
      type: str
    distro:
      description: The Linux distribution.
      type: str
    status:
      description: The image status.
      type: str
    description:
      description: Image description.
      type: str
    gpu_driver_version:
      description: Included GPU driver version.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.stevefulme1.nvidia_ai_factory.plugins.module_utils.nvidia_common import (
    NVIDIA_COMMON_ARGS,
    to_dict,
)
from ansible_collections.stevefulme1.nvidia_ai_factory.plugins.module_utils.nvidia_auth import (
    create_bcm_client,
)


def main():
    argument_spec = dict(
        name=dict(type="str"),
        architecture=dict(type="str", choices=["x86_64", "aarch64"]),
        distro=dict(type="str"),
    )
    argument_spec.update(NVIDIA_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    session = create_bcm_client(module)
    bcm_url = module.params["bcm_url"].rstrip("/")

    params = {}
    if module.params.get("name"):
        params["name"] = module.params["name"]
    if module.params.get("architecture"):
        params["architecture"] = module.params["architecture"]
    if module.params.get("distro"):
        params["distro"] = module.params["distro"]

    try:
        resp = session.get(
            "{0}/api/v1/software-images".format(bcm_url),
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        module.fail_json(
            msg="Failed to query software images: {0}".format(exc)
        )

    images = data if isinstance(data, list) else data.get("data", data.get("images", []))

    module.exit_json(changed=False, images=[to_dict(img) for img in images])


if __name__ == "__main__":
    main()
