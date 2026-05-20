#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: dgx_thermal_info
short_description: Get thermal and cooling status from DGX via Redfish
version_added: "1.0.0"
description:
    - Retrieves thermal sensor readings and fan status from an
      NVIDIA DGX node via the DMTF Redfish API on the BMC.
    - Queries the Chassis Thermal resource for temperature sensors
      and fan readings.
author:
    - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
    - stevefulme1.gpu_ai_factory.dgx_redfish
options:
    chassis_id:
        description:
            - Redfish Chassis ID.
            - Defaults to C(1) which is correct for single-chassis DGX nodes.
        type: str
        default: "1"
requirements:
    - requests
"""

EXAMPLES = r"""
- name: Get thermal status
  stevefulme1.gpu_ai_factory.dgx_thermal_info:
    bmc_host: dgx-01-bmc.example.com
    bmc_username: admin
    bmc_password: "{{ vault_bmc_password }}"
  register: thermal_info

- name: Show high temperatures
  ansible.builtin.debug:
    msg: "{{ item.name }}: {{ item.reading_celsius }}C"
  loop: "{{ thermal_info.temperatures }}"
  when: item.reading_celsius | int > 80
"""

RETURN = r"""
temperatures:
    description: List of temperature sensor readings.
    type: list
    elements: dict
    returned: always
    contains:
        name:
            description: Sensor name.
            type: str
            returned: always
        reading_celsius:
            description: Current temperature reading in Celsius.
            type: float
            returned: always
        upper_threshold_critical:
            description: Critical temperature threshold in Celsius.
            type: float
            returned: always
        health:
            description: Sensor health status.
            type: str
            returned: always
fans:
    description: List of fan readings.
    type: list
    elements: dict
    returned: always
    contains:
        name:
            description: Fan name.
            type: str
            returned: always
        reading_rpm:
            description: Current fan speed in RPM.
            type: int
            returned: always
        health:
            description: Fan health status.
            type: str
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
        chassis_id=dict(type="str", default="1"),
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

    thermal_path = "/redfish/v1/Chassis/{0}/Thermal".format(p["chassis_id"])
    try:
        data = client.get(thermal_path)
    except Exception as exc:
        module.fail_json(msg="Failed to query thermal data: {0}".format(exc))

    temperatures = []
    for temp in data.get("Temperatures", []):
        status = temp.get("Status", {})
        temperatures.append(dict(
            name=temp.get("Name", ""),
            reading_celsius=temp.get("ReadingCelsius", 0),
            upper_threshold_critical=temp.get("UpperThresholdCritical", 0),
            health=status.get("Health", ""),
        ))

    fans = []
    for fan in data.get("Fans", []):
        status = fan.get("Status", {})
        fans.append(dict(
            name=fan.get("Name", fan.get("FanName", "")),
            reading_rpm=fan.get("Reading", 0),
            health=status.get("Health", ""),
        ))

    module.exit_json(changed=False, temperatures=temperatures, fans=fans)


if __name__ == "__main__":
    main()
