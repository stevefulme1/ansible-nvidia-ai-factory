#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: bcm_monitoring
short_description: Configure BCM monitoring and health checks
version_added: "1.0.0"
description:
  - Create, update, or delete monitoring configurations in NVIDIA Base
    Command Manager.
  - Supports health check definitions for GPU nodes, InfiniBand fabric,
    storage systems, and custom metrics.
  - Monitoring configurations define what metrics are collected, alerting
    thresholds, and health check intervals.
  - Supports check mode for safe plan/preview operations.
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - The name of the monitoring configuration.
    type: str
    required: true
  state:
    description:
      - The desired state of the monitoring configuration.
    type: str
    choices:
      - present
      - absent
    default: present
  description:
    description:
      - A human-readable description of the monitoring rule.
    type: str
  monitor_type:
    description:
      - The type of monitoring to configure.
    type: str
    choices:
      - gpu_health
      - infiniband
      - storage
      - node_health
      - custom
    default: node_health
  enabled:
    description:
      - Whether the monitoring configuration is active.
    type: bool
    default: true
  check_interval:
    description:
      - The interval in seconds between health checks.
    type: int
    default: 60
  metrics:
    description:
      - List of metrics to collect.
      - Available metrics depend on the I(monitor_type).
    type: list
    elements: str
    default: []
  alert_thresholds:
    description:
      - Dictionary of metric thresholds that trigger alerts.
      - Keys are metric names, values are threshold configurations.
    type: dict
    default: {}
  alert_action:
    description:
      - Action to take when a threshold is exceeded.
    type: str
    choices:
      - log
      - email
      - webhook
      - drain_node
    default: log
  alert_recipients:
    description:
      - List of email addresses or webhook URLs for alert notifications.
    type: list
    elements: str
    default: []
  node_categories:
    description:
      - List of node categories to apply this monitoring to.
      - If empty, monitoring applies to all nodes.
    type: list
    elements: str
    default: []
extends_documentation_fragment:
  - stevefulme1.nvidia_ai_factory.nvidia
"""

EXAMPLES = r"""
- name: Configure GPU health monitoring
  stevefulme1.nvidia_ai_factory.bcm_monitoring:
    bcm_url: https://bcm.example.com
    bcm_token: "{{ bcm_token }}"
    name: gpu-health-check
    monitor_type: gpu_health
    check_interval: 30
    metrics:
      - gpu_temperature
      - gpu_utilization
      - gpu_memory_used
      - ecc_errors
    alert_thresholds:
      gpu_temperature:
        warning: 80
        critical: 90
      ecc_errors:
        critical: 1
    alert_action: email
    alert_recipients:
      - ops@example.com
    state: present

- name: Configure InfiniBand fabric monitoring
  stevefulme1.nvidia_ai_factory.bcm_monitoring:
    bcm_url: https://bcm.example.com
    bcm_token: "{{ bcm_token }}"
    name: ib-fabric-check
    monitor_type: infiniband
    check_interval: 60
    metrics:
      - link_errors
      - port_status
      - bandwidth_utilization
    alert_thresholds:
      link_errors:
        critical: 10
    alert_action: webhook
    alert_recipients:
      - https://hooks.example.com/alert
    state: present

- name: Disable a monitoring configuration
  stevefulme1.nvidia_ai_factory.bcm_monitoring:
    bcm_url: https://bcm.example.com
    bcm_token: "{{ bcm_token }}"
    name: gpu-health-check
    enabled: false
    state: present

- name: Remove monitoring configuration
  stevefulme1.nvidia_ai_factory.bcm_monitoring:
    bcm_url: https://bcm.example.com
    bcm_token: "{{ bcm_token }}"
    name: old-check
    state: absent
"""

RETURN = r"""
monitoring:
  description: The monitoring configuration details after the operation.
  returned: success and state is present
  type: dict
  contains:
    name:
      description: The monitoring configuration name.
      type: str
    id:
      description: The unique monitoring configuration identifier.
      type: str
    monitor_type:
      description: The type of monitoring.
      type: str
    enabled:
      description: Whether the monitoring is active.
      type: bool
    check_interval:
      description: The check interval in seconds.
      type: int
    metrics:
      description: List of collected metrics.
      type: list
    status:
      description: The monitoring status.
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


def get_monitoring(session, bcm_url, name):
    """Get a monitoring configuration by name."""
    try:
        resp = session.get(
            "{0}/api/v1/monitoring".format(bcm_url),
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
        monitor_type=dict(
            type="str",
            default="node_health",
            choices=["gpu_health", "infiniband", "storage", "node_health", "custom"],
        ),
        enabled=dict(type="bool", default=True),
        check_interval=dict(type="int", default=60),
        metrics=dict(type="list", elements="str", default=[]),
        alert_thresholds=dict(type="dict", default={}),
        alert_action=dict(
            type="str",
            default="log",
            choices=["log", "email", "webhook", "drain_node"],
        ),
        alert_recipients=dict(type="list", elements="str", default=[]),
        node_categories=dict(type="list", elements="str", default=[]),
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

    existing = get_monitoring(session, bcm_url, name)

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        mon_id = existing.get("id", existing.get("name"))
        try:
            session.delete(
                "{0}/api/v1/monitoring/{1}".format(bcm_url, mon_id),
                timeout=30,
            )
        except Exception as exc:
            module.fail_json(
                msg="Failed to delete monitoring config: {0}".format(exc)
            )
        module.exit_json(changed=True)

    # state == present
    payload = {
        "name": name,
        "monitor_type": module.params["monitor_type"],
        "enabled": module.params["enabled"],
        "check_interval": module.params["check_interval"],
        "alert_action": module.params["alert_action"],
    }
    if module.params.get("description"):
        payload["description"] = module.params["description"]
    if module.params["metrics"]:
        payload["metrics"] = module.params["metrics"]
    if module.params["alert_thresholds"]:
        payload["alert_thresholds"] = module.params["alert_thresholds"]
    if module.params["alert_recipients"]:
        payload["alert_recipients"] = module.params["alert_recipients"]
    if module.params["node_categories"]:
        payload["node_categories"] = module.params["node_categories"]

    if existing is None:
        if module.check_mode:
            module.exit_json(changed=True, monitoring=payload)
        try:
            resp = session.post(
                "{0}/api/v1/monitoring".format(bcm_url),
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            result = resp.json()
        except Exception as exc:
            module.fail_json(
                msg="Failed to create monitoring config: {0}".format(exc)
            )
        module.exit_json(changed=True, monitoring=to_dict(result))
    else:
        changed = False
        for key, value in payload.items():
            if key == "name":
                continue
            if existing.get(key) != value:
                changed = True
                break
        if not changed:
            module.exit_json(changed=False, monitoring=to_dict(existing))
        if module.check_mode:
            module.exit_json(changed=True, monitoring=payload)
        mon_id = existing.get("id", existing.get("name"))
        try:
            resp = session.put(
                "{0}/api/v1/monitoring/{1}".format(bcm_url, mon_id),
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            result = resp.json()
        except Exception as exc:
            module.fail_json(
                msg="Failed to update monitoring config: {0}".format(exc)
            )
        module.exit_json(changed=True, monitoring=to_dict(result))


if __name__ == "__main__":
    main()
