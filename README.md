# stevefulme1.nvidia_ai_factory

Ansible Collection for NVIDIA AI Factory / Sovereign AI Factory automation.

Provides comprehensive automation for NVIDIA Base Command Manager (BCM),
DGX/HGX systems, GPU allocation, tenant isolation, InfiniBand/RDMA networking,
NeMo model deployment, Triton Inference Server, and NGC catalog management.

## Requirements

- Ansible >= 2.16.0
- Python >= 3.12
- `requests` Python library

## Installation

```bash
ansible-galaxy collection install stevefulme1.nvidia_ai_factory
```

## Modules

### BCM Infrastructure
| Module | Description |
|--------|-------------|
| `bcm_cluster` | Manage BCM clusters |
| `bcm_cluster_info` | List/get BCM clusters |
| `bcm_node` | Manage DGX/HGX nodes |
| `bcm_node_info` | List/get nodes with GPU details |
| `bcm_tenant` | Manage BCM tenants |
| `bcm_tenant_info` | List tenants |
| `bcm_gpu_allocation` | Allocate/deallocate GPU slices |
| `bcm_gpu_allocation_info` | List GPU allocations |
| `bcm_job` | Submit/manage BCM jobs |
| `bcm_job_info` | List/get job status |

### DGX Hardware
| Module | Description |
|--------|-------------|
| `dgx_firmware` | Manage DGX firmware updates |
| `dgx_firmware_info` | Get firmware versions |
| `dgx_health` | Query DGX health via Redfish |
| `dgx_power` | Manage DGX power state |
| `dgx_bios` | Configure DGX BIOS settings |

### NVIDIA AI Software
| Module | Description |
|--------|-------------|
| `nemo_model` | Deploy/manage NeMo models |
| `nemo_model_info` | List deployed NeMo models |
| `triton_server` | Manage Triton Inference Server |
| `triton_model` | Load/unload Triton models |
| `ngc_image` | Pull/manage NGC container images |

### Network
| Module | Description |
|--------|-------------|
| `infiniband_port` | Configure InfiniBand ports |
| `infiniband_partition` | Manage IB partitions |
| `infiniband_info` | Query IB fabric status |
| `nvlink_info` | Query NVLink topology |
| `rdma_config` | Configure RDMA settings |

## Inventory Plugin

`nvidia_bcm_inventory` — Dynamic inventory from BCM API with automatic
grouping by node type and GPU model.

## Roles

| Role | Description |
|------|-------------|
| `dgx_provision` | Full DGX node provisioning |
| `gpu_allocation` | Allocate GPU slices to tenant |
| `tenant_isolation` | Configure tenant isolation |
| `infiniband_rdma` | Configure IB RDMA for multi-node training |
| `virtual_media_boot` | DGX provisioning via virtual media |
| `nemo_deploy` | Deploy NeMo models with Triton |

## EDA Event Sources

| Plugin | Description |
|--------|-------------|
| `dgx_telemetry` | Stream DGX health via Redfish/IPMI |
| `infiniband_fabric` | Monitor IB fabric events |
| `ngc_catalog` | Watch NGC catalog for new releases |

## License

GPL-3.0-or-later
