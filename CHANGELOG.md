# Changelog

## 2.0.0 (2026-05-20)

### Removed

- **All 50 modules deleted** -- every module used fabricated REST API endpoints
  (`/api/v1/clusters`, `/api/v1/dgx/bios`, `/api/v1/gaudi/configs`,
  `/api/v1/infiniband/fabric`, etc.) that do not match any real vendor API.
  Real BCM uses CMDaemon on port 8081; real Triton uses KServe v2; real NGC
  uses `api.ngc.nvidia.com/v2/`.
- **3 lookup plugins deleted** (bcm_nodes, dgx_categories, dgx_images) --
  fabricated BCM endpoints.
- **Inventory plugin deleted** (nvidia_bcm_inventory) -- fabricated
  `/api/v1/nodes` endpoint.
- **6 roles deleted** (dgx_provision, gpu_allocation, infiniband_rdma,
  nemo_deploy, tenant_isolation, virtual_media_boot) -- referenced deleted
  modules.
- **1 EDA plugin deleted** (infiniband_fabric) -- fabricated endpoint.
- **module_utils** (nvidia_auth, nvidia_common, nvidia_wait) and
  **doc_fragments** (nvidia) deleted.

### Retained

- 5 infrastructure roles using standard Ansible builtins.
- 4 filter plugins (data transformation only).
- 2 EDA plugins using real APIs (dgx_telemetry via Redfish, ngc_catalog via
  real NGC API).

## 1.1.1 (2026-05-18)

### Security

- Added `secret: true` to lookup and inventory plugin options.

## 1.1.0 (2026-05-18)

### New Features

- AMD MI300X, Intel Gaudi, credential management, and subscription calculator
  modules (now deleted).
- Security compliance roles (stig_dgx, cis_ai_cluster) -- retained.
- Vault integration and PS bundle roles -- retained.

## 1.0.0 (2026-05-17)

### Added

- Initial release with NVIDIA BCM, DGX, InfiniBand, NeMo, Triton, and NGC
  modules (now deleted).
