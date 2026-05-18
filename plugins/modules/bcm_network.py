#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: bcm_network
short_description: Manage BCM network configurations
version_added: "1.0.0"
description:
  - Create, update, or delete network configurations in NVIDIA Base
    Command Manager.
  - Supports both InfiniBand and Ethernet network types commonly used
    in DGX/HGX GPU clusters.
  - InfiniBand networks are critical for GPU-to-GPU RDMA communication
    in AI training workloads.
  - Supports check mode for safe plan/preview operations.
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - The name of the network configuration.
    type: str
    required: true
  state:
    description:
      - The desired state of the network configuration.
    type: str
    choices:
      - present
      - absent
    default: present
  description:
    description:
      - A human-readable description of the network.
    type: str
  network_type:
    description:
      - The type of network.
    type: str
    choices:
      - infiniband
      - ethernet
    default: ethernet
  subnet:
    description:
      - The subnet CIDR for the network (e.g., C(10.0.0.0/24)).
    type: str
  gateway:
    description:
      - The default gateway address.
    type: str
  vlan_id:
    description:
      - The VLAN ID for the network, if applicable.
    type: int
  mtu:
    description:
      - The MTU size for the network interface.
      - InfiniBand networks typically use 4096 or higher.
    type: int
    default: 1500
  ib_partition_key:
    description:
      - The InfiniBand partition key (P_Key) for fabric isolation.
      - Only applicable when I(network_type=infiniband).
    type: str
  rdma_enabled:
    description:
      - Whether RDMA (Remote Direct Memory Access) is enabled.
      - Required for GPU Direct RDMA in training workloads.
    type: bool
    default: false
extends_documentation_fragment:
  - stevefulme1.nvidia_ai_factory.nvidia
"""

EXAMPLES = r"""
- name: Create an InfiniBand network for GPU RDMA
  stevefulme1.nvidia_ai_factory.bcm_network:
    bcm_url: https://bcm.example.com
    bcm_token: "{{ bcm_token }}"
    name: ib-gpu-fabric
    network_type: infiniband
    subnet: "10.10.0.0/16"
    mtu: 4096
    rdma_enabled: true
    ib_partition_key: "0x8001"
    state: present

- name: Create an Ethernet management network
  stevefulme1.nvidia_ai_factory.bcm_network:
    bcm_url: https://bcm.example.com
    bcm_token: "{{ bcm_token }}"
    name: mgmt-network
    network_type: ethernet
    subnet: "192.168.1.0/24"
    gateway: "192.168.1.1"
    vlan_id: 100
    state: present

- name: Delete a network configuration
  stevefulme1.nvidia_ai_factory.bcm_network:
    bcm_url: https://bcm.example.com
    bcm_token: "{{ bcm_token }}"
    name: old-network
    state: absent
"""

RETURN = r"""
network:
  description: The network configuration details after the operation.
  returned: success and state is present
  type: dict
  contains:
    name:
      description: The network name.
      type: str
    id:
      description: The unique network identifier.
      type: str
    network_type:
      description: The network type (infiniband or ethernet).
      type: str
    subnet:
      description: The subnet CIDR.
      type: str
    status:
      description: The network status.
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


def get_network(session, bcm_url, name):
    """Get a network configuration by name."""
    try:
        resp = session.get(
            "{0}/api/v1/networks".format(bcm_url),
            params={"name": name},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        networks = data if isinstance(data, list) else data.get("data", [])
        for net in networks:
            if net.get("name") == name:
                return net
    except Exception:
        pass
    return None


def main():
    argument_spec = dict(
        name=dict(type="str", required=True),
        state=dict(type="str", default="present", choices=["present", "absent"]),
        description=dict(type="str"),
        network_type=dict(
            type="str", default="ethernet", choices=["infiniband", "ethernet"]
        ),
        subnet=dict(type="str"),
        gateway=dict(type="str"),
        vlan_id=dict(type="int"),
        mtu=dict(type="int", default=1500),
        ib_partition_key=dict(type="str"),
        rdma_enabled=dict(type="bool", default=False),
    )
    argument_spec.update(NVIDIA_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    session = create_bcm_client(module)
    bcm_url = module.params["bcm_url"].rstrip("/")
    name = module.params["name"]
    state = module.params["state"]

    existing = get_network(session, bcm_url, name)

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        net_id = existing.get("id", existing.get("name"))
        try:
            session.delete(
                "{0}/api/v1/networks/{1}".format(bcm_url, net_id),
                timeout=30,
            )
        except Exception as exc:
            module.fail_json(msg="Failed to delete network: {0}".format(exc))
        module.exit_json(changed=True)

    # state == present
    payload = {"name": name, "network_type": module.params["network_type"]}
    for key in ("description", "subnet", "gateway", "ib_partition_key"):
        if module.params.get(key):
            payload[key] = module.params[key]
    if module.params.get("vlan_id") is not None:
        payload["vlan_id"] = module.params["vlan_id"]
    payload["mtu"] = module.params["mtu"]
    payload["rdma_enabled"] = module.params["rdma_enabled"]

    if existing is None:
        if module.check_mode:
            module.exit_json(changed=True, network=payload)
        try:
            resp = session.post(
                "{0}/api/v1/networks".format(bcm_url),
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            result = resp.json()
        except Exception as exc:
            module.fail_json(msg="Failed to create network: {0}".format(exc))
        module.exit_json(changed=True, network=to_dict(result))
    else:
        changed = False
        for key, value in payload.items():
            if key == "name":
                continue
            if existing.get(key) != value:
                changed = True
                break
        if not changed:
            module.exit_json(changed=False, network=to_dict(existing))
        if module.check_mode:
            module.exit_json(changed=True, network=payload)
        net_id = existing.get("id", existing.get("name"))
        try:
            resp = session.put(
                "{0}/api/v1/networks/{1}".format(bcm_url, net_id),
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            result = resp.json()
        except Exception as exc:
            module.fail_json(msg="Failed to update network: {0}".format(exc))
        module.exit_json(changed=True, network=to_dict(result))


if __name__ == "__main__":
    main()
