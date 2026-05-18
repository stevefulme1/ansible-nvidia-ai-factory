# Changelog

## 1.0.0 (2026-05-18)

### New Features

- **BCM Infrastructure modules**: `bcm_cluster`, `bcm_cluster_info`, `bcm_node`,
  `bcm_node_info`, `bcm_tenant`, `bcm_tenant_info`, `bcm_gpu_allocation`,
  `bcm_gpu_allocation_info`, `bcm_job`, `bcm_job_info`
- **DGX Hardware modules**: `dgx_firmware`, `dgx_firmware_info`, `dgx_health`,
  `dgx_power`, `dgx_bios`
- **NVIDIA AI Software modules**: `nemo_model`, `nemo_model_info`,
  `triton_server`, `triton_model`, `ngc_image`
- **Network modules**: `infiniband_port`, `infiniband_partition`,
  `infiniband_info`, `nvlink_info`, `rdma_config`
- **Inventory plugin**: `nvidia_bcm_inventory` dynamic inventory from BCM API
- **Roles**: `dgx_provision`, `gpu_allocation`, `tenant_isolation`,
  `infiniband_rdma`, `virtual_media_boot`, `nemo_deploy`
- **EDA event sources**: `dgx_telemetry`, `infiniband_fabric`, `ngc_catalog`
- **EDA rulebooks**: `dgx_health`, `infiniband_monitor`, `gpu_utilization`
