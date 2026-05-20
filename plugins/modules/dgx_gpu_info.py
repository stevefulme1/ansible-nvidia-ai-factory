#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: dgx_gpu_info
short_description: Get GPU inventory and health from DGX via Redfish
version_added: "1.0.0"
description:
    - Retrieves GPU accelerator inventory from an NVIDIA DGX node
      using the DMTF Redfish API on the BMC.
    - GPUs appear as processors with C(ProcessorType=GPU) in the
      Redfish Processors collection.
author:
    - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
    - stevefulme1.gpu_ai_factory.dgx_redfish
requirements:
    - requests
"""

EXAMPLES = r"""
- name: Get GPU inventory
  stevefulme1.gpu_ai_factory.dgx_gpu_info:
    bmc_host: dgx-01-bmc.example.com
    bmc_username: admin
    bmc_password: "{{ vault_bmc_password }}"
  register: gpu_info

- name: Show GPU count
  ansible.builtin.debug:
    msg: "GPU count: {{ gpu_info.gpus | length }}"
"""

RETURN = r"""
gpus:
    description: List of GPU accelerator details.
    type: list
    elements: dict
    returned: always
    contains:
        id:
            description: Redfish processor ID.
            type: str
            returned: always
        name:
            description: GPU name.
            type: str
            returned: always
        model:
            description: GPU model string (e.g. C(NVIDIA H100 80GB HBM3)).
            type: str
            returned: always
        manufacturer:
            description: GPU manufacturer.
            type: str
            returned: always
        health:
            description: GPU health status.
            type: str
            returned: always
        state:
            description: GPU enabled state.
            type: str
            returned: always
gpu_count:
    description: Total number of GPUs found.
    type: int
    returned: always
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from ansible_collections.stevefulme1.gpu_ai_factory.plugins.module_utils.redfish_client import (
        RedfishClient,
    )
    HAS_REDFISH = True
except ImportError:
    HAS_REDFISH = False


def main():
    argument_spec = dict(
        bmc_host=dict(type="str", required=True),
        bmc_username=dict(type="str", required=True),
        bmc_password=dict(type="str", required=True, no_log=True),
        validate_certs=dict(type="bool", default=True),
        system_id=dict(type="str", default="1"),
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_REDFISH:
        module.fail_json(msg="The 'requests' library is required.")

    p = module.params
    client = RedfishClient(
        base_url="https://{0}".format(p["bmc_host"]),
        username=p["bmc_username"],
        password=p["bmc_password"],
        validate_certs=p["validate_certs"],
    )

    # Get processor collection
    proc_path = "/redfish/v1/Systems/{0}/Processors".format(p["system_id"])
    try:
        proc_data = client.get(proc_path)
    except Exception as exc:
        module.fail_json(msg="Failed to query processors: {0}".format(exc))

    gpus = []
    members = proc_data.get("Members", [])
    for member in members:
        uri = member.get("@odata.id", "")
        if not uri:
            continue
        try:
            proc = client.get(uri)
        except Exception:
            continue

        if proc.get("ProcessorType", "") != "GPU":
            continue

        status = proc.get("Status", {})
        gpus.append(dict(
            id=proc.get("Id", ""),
            name=proc.get("Name", ""),
            model=proc.get("Model", ""),
            manufacturer=proc.get("Manufacturer", ""),
            health=status.get("Health", ""),
            state=status.get("State", ""),
        ))

    module.exit_json(changed=False, gpus=gpus, gpu_count=len(gpus))


if __name__ == "__main__":
    main()
