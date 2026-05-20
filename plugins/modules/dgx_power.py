#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: dgx_power
short_description: Manage DGX power state via Redfish
version_added: "1.0.0"
description:
    - Controls the power state of an NVIDIA DGX node via the DMTF
      Redfish API ComputerSystem.Reset action on the BMC.
    - Supports power on, graceful shutdown, force off, and restart.
author:
    - Steve Fulmer (@stevefulme1)
options:
    state:
        description:
            - Desired power action.
        type: str
        required: true
        choices:
            - "on"
            - "off"
            - "force_off"
            - "restart"
            - "force_restart"
extends_documentation_fragment:
    - stevefulme1.gpu_ai_factory.dgx_redfish
requirements:
    - requests
"""

EXAMPLES = r"""
- name: Power on the DGX node
  stevefulme1.gpu_ai_factory.dgx_power:
    bmc_host: dgx-01-bmc.example.com
    bmc_username: admin
    bmc_password: "{{ vault_bmc_password }}"
    state: "on"

- name: Graceful restart
  stevefulme1.gpu_ai_factory.dgx_power:
    bmc_host: dgx-01-bmc.example.com
    bmc_username: admin
    bmc_password: "{{ vault_bmc_password }}"
    state: restart
"""

RETURN = r"""
power_state:
    description: Power state after the action.
    type: str
    returned: always
msg:
    description: Human-readable result message.
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

STATE_MAP = {
    "on": "On",
    "off": "GracefulShutdown",
    "force_off": "ForceOff",
    "restart": "GracefulRestart",
    "force_restart": "ForceRestart",
}


def main():
    argument_spec = dict(
        bmc_host=dict(type="str", required=True),
        bmc_username=dict(type="str", required=True),
        bmc_password=dict(type="str", required=True, no_log=True),
        validate_certs=dict(type="bool", default=True),
        system_id=dict(type="str", default="1"),
        state=dict(
            type="str", required=True,
            choices=["on", "off", "force_off", "restart", "force_restart"],
        ),
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_REDFISH:
        module.fail_json(msg="The 'requests' library is required.")

    p = module.params
    reset_type = STATE_MAP[p["state"]]

    client = RedfishClient(
        base_url="https://{0}".format(p["bmc_host"]),
        username=p["bmc_username"],
        password=p["bmc_password"],
        validate_certs=p["validate_certs"],
    )

    # Check current state
    try:
        data = client.get("/redfish/v1/Systems/{0}".format(p["system_id"]))
    except Exception as exc:
        module.fail_json(msg="Failed to query Redfish: {0}".format(exc))

    current = data.get("PowerState", "")

    # In check mode, report what would change
    if module.check_mode:
        would_change = not (
            (p["state"] == "on" and current == "On")
            or (p["state"] in ("off", "force_off") and current == "Off")
        )
        module.exit_json(
            changed=would_change,
            power_state=current,
            msg="Would send {0} action".format(reset_type),
        )

    # Skip if already in desired state
    if p["state"] == "on" and current == "On":
        module.exit_json(
            changed=False, power_state=current,
            msg="System is already powered on",
        )
    if p["state"] in ("off", "force_off") and current == "Off":
        module.exit_json(
            changed=False, power_state=current,
            msg="System is already powered off",
        )

    # Send reset action
    action_path = "/redfish/v1/Systems/{0}/Actions/ComputerSystem.Reset".format(
        p["system_id"]
    )
    try:
        client.post(action_path, payload={"ResetType": reset_type})
    except Exception as exc:
        module.fail_json(msg="Failed to set power state: {0}".format(exc))

    module.exit_json(
        changed=True,
        power_state=reset_type,
        msg="Sent {0} action successfully".format(reset_type),
    )


if __name__ == "__main__":
    main()
