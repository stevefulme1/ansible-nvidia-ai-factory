#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: dgx_system_info
short_description: Get DGX system information via Redfish
version_added: "1.0.0"
description:
    - Retrieves system information from an NVIDIA DGX node via the
      DMTF Redfish API on the BMC.
    - Returns model, serial number, health status, BIOS version,
      processor summary, and memory summary.
author:
    - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
    - stevefulme1.gpu_ai_factory.dgx_redfish
requirements:
    - requests
"""

EXAMPLES = r"""
- name: Get DGX system info
  stevefulme1.gpu_ai_factory.dgx_system_info:
    bmc_host: dgx-01-bmc.example.com
    bmc_username: admin
    bmc_password: "{{ vault_bmc_password }}"
  register: sys_info

- name: Show system model
  ansible.builtin.debug:
    msg: "Model: {{ sys_info.system.model }}"
"""

RETURN = r"""
system:
    description: DGX system information.
    type: dict
    returned: always
    contains:
        id:
            description: Redfish System ID.
            type: str
            returned: always
        name:
            description: System name.
            type: str
            returned: always
        model:
            description: System model (e.g. C(NVIDIA DGX H100)).
            type: str
            returned: always
        manufacturer:
            description: System manufacturer.
            type: str
            returned: always
        serial_number:
            description: System serial number.
            type: str
            returned: always
        bios_version:
            description: BIOS firmware version string.
            type: str
            returned: always
        health:
            description: Overall system health status.
            type: str
            returned: always
        power_state:
            description: Current power state.
            type: str
            returned: always
        processor_count:
            description: Number of installed processors.
            type: int
            returned: always
        total_memory_gb:
            description: Total system memory in GiB.
            type: float
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

    try:
        data = client.get("/redfish/v1/Systems/{0}".format(p["system_id"]))
    except Exception as exc:
        module.fail_json(msg="Failed to query Redfish: {0}".format(exc))

    proc_summary = data.get("ProcessorSummary", {})
    mem_summary = data.get("MemorySummary", {})

    system = dict(
        id=data.get("Id", ""),
        name=data.get("Name", ""),
        model=data.get("Model", ""),
        manufacturer=data.get("Manufacturer", ""),
        serial_number=data.get("SerialNumber", ""),
        bios_version=data.get("BiosVersion", ""),
        health=data.get("Status", {}).get("Health", ""),
        power_state=data.get("PowerState", ""),
        processor_count=proc_summary.get("Count", 0),
        total_memory_gb=mem_summary.get("TotalSystemMemoryGiB", 0),
    )

    module.exit_json(changed=False, system=system)


if __name__ == "__main__":
    main()
