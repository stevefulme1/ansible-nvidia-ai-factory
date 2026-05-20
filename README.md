> **EXPERIMENTAL** - This collection is a proof of concept and is not production ready.

# stevefulme1.gpu_ai_factory

Ansible Collection for GPU AI Factory infrastructure automation.

**Status: Pre-release. Under active development.**

> **Note:** All 50 custom modules, 3 lookup plugins, 1 inventory plugin, and
> 6 roles were removed during an audit because they used fabricated REST API
> endpoints (`/api/v1/clusters`, `/api/v1/dgx/bios`, `/api/v1/gaudi/configs`,
> etc.) that do not match any real NVIDIA, AMD, or Intel API.  Real BCM uses
> CMDaemon on port 8081 with a different endpoint structure; real Triton uses
> the KServe v2 inference protocol; real InfiniBand uses `ibstat`/`ibnetdiscover`
> CLI tools.

## Remaining Content

### Roles (5)

Infrastructure roles using standard Ansible builtins:

| Role | Description |
|---|---|
| `cis_ai_cluster` | CIS benchmark hardening for AI clusters |
| `ps_lab_setup` | Professional Services demo lab environment |
| `reference_deployment` | AI Factory reference architecture deployment |
| `stig_dgx` | DISA STIG hardening for DGX nodes |
| `vault_integration` | HashiCorp Vault configuration for AI Factory |

### Filter Plugins (4)

Data-transformation filters for GPU node data:

| Filter | Description |
|---|---|
| `gpu_memory_total` | Sum GPU memory across nodes |
| `gpu_count` | Count GPUs across nodes |
| `filter_by_gpu_type` | Filter nodes by GPU type |
| `gpu_utilization_avg` | Average GPU utilization from telemetry |

### EDA Plugins (2)

| Plugin | Type | Description |
|---|---|---|
| `dgx_telemetry` | Event source | DGX telemetry via real Redfish API |
| `ngc_catalog` | Event source | NGC catalog updates via real NGC API |

## Requirements

- Ansible >= 2.16.0
- Python >= 3.12

## Installation

```bash
ansible-galaxy collection install stevefulme1.gpu_ai_factory
```

## License

GNU General Public License v3.0 or later.
