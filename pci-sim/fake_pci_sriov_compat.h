/* SPDX-License-Identifier: GPL-2.0 */
#ifndef FAKE_PCI_SRIOV_COMPAT_H
#define FAKE_PCI_SRIOV_COMPAT_H

#include <linux/version.h>

/*
 * Keep kernel API compatibility decisions in one place.  The module is
 * developed against newer upstream/Ubuntu kernels, while Debian 13 currently
 * ships a 6.12 kernel whose IOMMU and VFIO callback tables predate some of the
 * newer PASID/HWPT and VFIO region-info hooks.
 *
 * These version gates intentionally select the conservative 6.12-compatible
 * API for older kernels.  Newer kernels keep using the richer callbacks.
 */

/* iommu_domain_ops.attach_dev gained the previous-domain argument later. */
#if KERNEL_VERSION(6, 15, 0) <= LINUX_VERSION_CODE
#define PCI_SIM_IOMMU_ATTACH_HAS_OLD_DOMAIN 1
#else
#define PCI_SIM_IOMMU_ATTACH_HAS_OLD_DOMAIN 0
#endif

/* iommu_ops.domain_alloc_paging_flags and IOMMU_HWPT_ALLOC_PASID are newer. */
#if KERNEL_VERSION(6, 15, 0) <= LINUX_VERSION_CODE
#define PCI_SIM_IOMMU_HAS_DOMAIN_ALLOC_PAGING_FLAGS 1
#else
#define PCI_SIM_IOMMU_HAS_DOMAIN_ALLOC_PAGING_FLAGS 0
#endif

/* VFIO grew optional region-info and PASID/token callbacks after 6.12. */
#if KERNEL_VERSION(6, 15, 0) <= LINUX_VERSION_CODE
#define PCI_SIM_VFIO_HAS_GET_REGION_INFO_CAPS 1
#define PCI_SIM_VFIO_HAS_MATCH_TOKEN_UUID 1
#define PCI_SIM_VFIO_HAS_PASID_IOAS 1
#else
#define PCI_SIM_VFIO_HAS_GET_REGION_INFO_CAPS 0
#define PCI_SIM_VFIO_HAS_MATCH_TOKEN_UUID 0
#define PCI_SIM_VFIO_HAS_PASID_IOAS 0
#endif

#endif /* FAKE_PCI_SRIOV_COMPAT_H */
