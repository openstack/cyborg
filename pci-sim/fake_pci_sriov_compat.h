/* SPDX-License-Identifier: GPL-2.0 */
#ifndef FAKE_PCI_SRIOV_COMPAT_H
#define FAKE_PCI_SRIOV_COMPAT_H

#include <linux/version.h>

/*
 * Keep kernel API compatibility decisions in one place.  The module is
 * developed against newer upstream/Ubuntu kernels, while Debian 13 and
 * CentOS Stream 10 currently ship a 6.12 kernel whose IOMMU and VFIO
 * callback tables predate some of the newer PASID/HWPT and VFIO
 * region-info hooks.
 *
 * CentOS Stream 10 backports the 6.15+ API changes into its 6.12
 * kernel, so LINUX_VERSION_CODE alone is insufficient.  The
 * RHEL_RELEASE_CODE macro (defined in CentOS/RHEL kernel headers)
 * gates the backported API at RHEL_RELEASE_VERSION(10, 3).
 *
 * These version gates intentionally select the conservative 6.12-compatible
 * API for older kernels.  Newer kernels keep using the richer callbacks.
 */

#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 15, 0)
#define PCI_SIM_HAS_615_API 1
#elif defined(RHEL_RELEASE_CODE)
#if RHEL_RELEASE_VERSION(10, 3) <= RHEL_RELEASE_CODE
#define PCI_SIM_HAS_615_API 1
#else
#define PCI_SIM_HAS_615_API 0
#endif
#else
#define PCI_SIM_HAS_615_API 0
#endif

/* iommu_domain_ops.attach_dev gained the previous-domain argument later. */
#define PCI_SIM_IOMMU_ATTACH_HAS_OLD_DOMAIN PCI_SIM_HAS_615_API
/* iommu_ops.domain_alloc_paging_flags and IOMMU_HWPT_ALLOC_PASID are newer. */
#define PCI_SIM_IOMMU_HAS_DOMAIN_ALLOC_PAGING_FLAGS PCI_SIM_HAS_615_API
/* VFIO grew optional region-info and PASID/token callbacks after 6.12. */
#define PCI_SIM_VFIO_HAS_GET_REGION_INFO_CAPS PCI_SIM_HAS_615_API
#define PCI_SIM_VFIO_HAS_MATCH_TOKEN_UUID PCI_SIM_HAS_615_API
#define PCI_SIM_VFIO_HAS_PASID_IOAS PCI_SIM_HAS_615_API

#endif /* FAKE_PCI_SRIOV_COMPAT_H */
