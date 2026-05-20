#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: dgx_firmware_info
short_description: Get firmware versions from DGX via Redfish
version_added: "1.0.0"
description:
    - Retrieves firmware inventory from an NVIDIA DGX node
      via the DMTF Redfish UpdateService FirmwareInventory collection.
    - Returns all firmware components including BIOS, BMC, GPU VBIOS,
      NIC firmware, and drive firmware.
author:
    - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
    - stevefulme1.gpu_ai_factory.dgx_redfish
requirements:
    - requests
"""

EXAMPLES = r"""
- name: Get firmware inventory
  stevefulme1.gpu_ai_factory.dgx_firmware_info:
    bmc_host: dgx-01-bmc.example.com
    bmc_username: admin
    bmc_password: "{{ vault_bmc_password }}"
  register: fw_info

- name: Show all firmware versions
  ansible.builtin.debug:
    msg: "{{ item.name }}: {{ item.version }}"
  loop: "{{ fw_info.firmware }}"
"""

RETURN = r"""
firmware:
    description: List of firmware components.
    type: list
    elements: dict
    returned: always
    contains:
        id:
            description: Firmware inventory ID.
            type: str
            returned: always
        name:
            description: Firmware component name.
            type: str
            returned: always
        version:
            description: Installed firmware version string.
            type: str
            returned: always
        updateable:
            description: Whether the component can be updated.
            type: bool
            returned: always
        health:
            description: Component health status.
            type: str
            returned: always
firmware_count:
    description: Total number of firmware components.
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

    fw_path = "/redfish/v1/UpdateService/FirmwareInventory"
    try:
        fw_data = client.get(fw_path)
    except Exception as exc:
        module.fail_json(msg="Failed to query firmware inventory: {0}".format(exc))

    firmware = []
    members = fw_data.get("Members", [])
    for member in members:
        uri = member.get("@odata.id", "")
        if not uri:
            continue
        try:
            fw = client.get(uri)
        except Exception:
            continue

        status = fw.get("Status", {})
        firmware.append(dict(
            id=fw.get("Id", ""),
            name=fw.get("Name", ""),
            version=fw.get("Version", ""),
            updateable=fw.get("Updateable", False),
            health=status.get("Health", "OK"),
        ))

    module.exit_json(changed=False, firmware=firmware, firmware_count=len(firmware))


if __name__ == "__main__":
    main()
