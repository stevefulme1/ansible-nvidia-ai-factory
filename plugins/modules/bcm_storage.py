#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: bcm_storage
short_description: Manage BCM shared storage configurations
version_added: "1.0.0"
description:
  - Create, update, or delete shared storage configurations in NVIDIA
    Base Command Manager.
  - Supports NFS, Lustre, and GPFS (Spectrum Scale) mount configurations
    used for shared datasets and model storage in AI Factory deployments.
  - Supports check mode for safe plan/preview operations.
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - The name of the storage configuration.
    type: str
    required: true
  state:
    description:
      - The desired state of the storage configuration.
    type: str
    choices:
      - present
      - absent
    default: present
  description:
    description:
      - A human-readable description of the storage mount.
    type: str
  storage_type:
    description:
      - The type of shared storage.
    type: str
    choices:
      - nfs
      - lustre
      - gpfs
    default: nfs
  server:
    description:
      - The storage server hostname or IP address.
    type: str
  export_path:
    description:
      - The export path on the storage server.
    type: str
  mount_point:
    description:
      - The local mount point on compute nodes.
    type: str
  mount_options:
    description:
      - Mount options as a comma-separated string.
    type: str
    default: "defaults"
  auto_mount:
    description:
      - Whether to automatically mount the storage at boot.
    type: bool
    default: true
  node_categories:
    description:
      - List of node categories that should mount this storage.
      - If empty, storage is available to all nodes.
    type: list
    elements: str
    default: []
extends_documentation_fragment:
  - stevefulme1.nvidia_ai_factory.nvidia
"""

EXAMPLES = r"""
- name: Configure NFS storage for training datasets
  stevefulme1.nvidia_ai_factory.bcm_storage:
    bcm_url: https://bcm.example.com
    bcm_token: "{{ bcm_token }}"
    name: training-data
    storage_type: nfs
    server: nfs-server.example.com
    export_path: /exports/training
    mount_point: /mnt/training
    mount_options: "rw,hard,intr,nfsvers=4.1"
    state: present

- name: Configure Lustre storage for model checkpoints
  stevefulme1.nvidia_ai_factory.bcm_storage:
    bcm_url: https://bcm.example.com
    bcm_token: "{{ bcm_token }}"
    name: model-checkpoints
    storage_type: lustre
    server: lustre-mgs.example.com
    export_path: /lustre/checkpoints
    mount_point: /mnt/checkpoints
    node_categories:
      - gpu-compute
      - gpu-training
    state: present

- name: Remove storage configuration
  stevefulme1.nvidia_ai_factory.bcm_storage:
    bcm_url: https://bcm.example.com
    bcm_token: "{{ bcm_token }}"
    name: old-storage
    state: absent
"""

RETURN = r"""
storage:
  description: The storage configuration details after the operation.
  returned: success and state is present
  type: dict
  contains:
    name:
      description: The storage configuration name.
      type: str
    id:
      description: The unique storage identifier.
      type: str
    storage_type:
      description: The storage type (nfs, lustre, gpfs).
      type: str
    server:
      description: The storage server address.
      type: str
    mount_point:
      description: The local mount point.
      type: str
    status:
      description: The storage mount status.
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


def get_storage(session, bcm_url, name):
    """Get a storage configuration by name."""
    try:
        resp = session.get(
            "{0}/api/v1/storage".format(bcm_url),
            params={"name": name},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        items = data if isinstance(data, list) else data.get("data", [])
        for item in items:
            if item.get("name") == name:
                return item
    except Exception:
        pass
    return None


def main():
    argument_spec = dict(
        name=dict(type="str", required=True),
        state=dict(type="str", default="present", choices=["present", "absent"]),
        description=dict(type="str"),
        storage_type=dict(
            type="str", default="nfs", choices=["nfs", "lustre", "gpfs"]
        ),
        server=dict(type="str"),
        export_path=dict(type="str"),
        mount_point=dict(type="str"),
        mount_options=dict(type="str", default="defaults"),
        auto_mount=dict(type="bool", default=True),
        node_categories=dict(type="list", elements="str", default=[]),
    )
    argument_spec.update(NVIDIA_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("server", "export_path", "mount_point"), True),
        ],
    )

    session = create_bcm_client(module)
    bcm_url = module.params["bcm_url"].rstrip("/")
    name = module.params["name"]
    state = module.params["state"]

    existing = get_storage(session, bcm_url, name)

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        stor_id = existing.get("id", existing.get("name"))
        try:
            session.delete(
                "{0}/api/v1/storage/{1}".format(bcm_url, stor_id),
                timeout=30,
            )
        except Exception as exc:
            module.fail_json(
                msg="Failed to delete storage configuration: {0}".format(exc)
            )
        module.exit_json(changed=True)

    # state == present
    payload = {
        "name": name,
        "storage_type": module.params["storage_type"],
        "mount_options": module.params["mount_options"],
        "auto_mount": module.params["auto_mount"],
    }
    for key in ("description", "server", "export_path", "mount_point"):
        if module.params.get(key):
            payload[key] = module.params[key]
    if module.params["node_categories"]:
        payload["node_categories"] = module.params["node_categories"]

    if existing is None:
        if module.check_mode:
            module.exit_json(changed=True, storage=payload)
        try:
            resp = session.post(
                "{0}/api/v1/storage".format(bcm_url),
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            result = resp.json()
        except Exception as exc:
            module.fail_json(
                msg="Failed to create storage configuration: {0}".format(exc)
            )
        module.exit_json(changed=True, storage=to_dict(result))
    else:
        changed = False
        for key, value in payload.items():
            if key == "name":
                continue
            if existing.get(key) != value:
                changed = True
                break
        if not changed:
            module.exit_json(changed=False, storage=to_dict(existing))
        if module.check_mode:
            module.exit_json(changed=True, storage=payload)
        stor_id = existing.get("id", existing.get("name"))
        try:
            resp = session.put(
                "{0}/api/v1/storage/{1}".format(bcm_url, stor_id),
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            result = resp.json()
        except Exception as exc:
            module.fail_json(
                msg="Failed to update storage configuration: {0}".format(exc)
            )
        module.exit_json(changed=True, storage=to_dict(result))


if __name__ == "__main__":
    main()
