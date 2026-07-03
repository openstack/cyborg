// SPDX-License-Identifier: GPL-2.0
/*
 * Fake PCI SR-IOV VFIO test fixture -- software IOMMU driver
 *
 * Implements a minimal IOMMU that claims all fake PCI domains and provides
 * software page-table tracking without any real DMA remapping.  Every fake
 * PCI device gets its own IOMMU group so VFIO can assign individual VFs.
 */

#include "fake_pci_sriov.h"

struct iommu_device fake_iommu_dev;
struct platform_device *fake_iommu_pdev;

struct fake_iommu_domain {
	struct iommu_domain domain;
	struct xarray mappings;
};

static struct fake_iommu_domain *to_fake_domain(struct iommu_domain *dom)
{
	return container_of(dom, struct fake_iommu_domain, domain);
}

static int fake_domain_attach(struct iommu_domain *domain, struct device *dev
#if PCI_SIM_IOMMU_ATTACH_HAS_OLD_DOMAIN
			      ,
			      struct iommu_domain *old
#endif
)
{
	dev_dbg(dev, "fake_iommu: attached to domain type %u\n", domain->type);
	return 0;
}

static const struct iommu_domain_ops fake_blocking_domain_ops = {
	.attach_dev = fake_domain_attach,
};

static struct iommu_domain fake_blocking_domain = {
	.type = IOMMU_DOMAIN_BLOCKED,
	.ops = &fake_blocking_domain_ops,
};

static void fake_domain_free_paging(struct iommu_domain *domain)
{
	struct fake_iommu_domain *fake_dom = to_fake_domain(domain);

	xa_destroy(&fake_dom->mappings);
	kfree(fake_dom);
}

static int fake_domain_map_pages(struct iommu_domain *domain,
				 unsigned long iova, phys_addr_t paddr,
				 size_t pgsize, size_t pgcount, int prot,
				 gfp_t gfp, size_t *mapped)
{
	struct fake_iommu_domain *fake_dom = to_fake_domain(domain);
	unsigned long iova_pfn = iova >> PAGE_SHIFT;
	unsigned long pfn = paddr >> PAGE_SHIFT;
	size_t total = pgsize * pgcount;
	size_t npages = total >> PAGE_SHIFT;
	size_t i;
	int ret;

	*mapped = 0;

	if (!IS_ALIGNED(iova, PAGE_SIZE) || !IS_ALIGNED(paddr, PAGE_SIZE) ||
	    !IS_ALIGNED(total, PAGE_SIZE))
		return -EINVAL;

	for (i = 0; i < npages; i++) {
		if (xa_load(&fake_dom->mappings, iova_pfn + i)) {
			ret = -EBUSY;
			goto err_unmap;
		}

		ret = xa_err(xa_store(&fake_dom->mappings, iova_pfn + i,
				      xa_mk_value(pfn + i), gfp));
		if (ret)
			goto err_unmap;

		*mapped += PAGE_SIZE;
	}

	return 0;

err_unmap:
	while (i--)
		xa_erase(&fake_dom->mappings, iova_pfn + i);
	*mapped = 0;
	return ret;
}

static size_t fake_domain_unmap_pages(struct iommu_domain *domain,
				      unsigned long iova, size_t pgsize,
				      size_t pgcount,
				      struct iommu_iotlb_gather *gather)
{
	struct fake_iommu_domain *fake_dom = to_fake_domain(domain);
	unsigned long iova_pfn = iova >> PAGE_SHIFT;
	size_t total = pgsize * pgcount;
	size_t npages = total >> PAGE_SHIFT;
	size_t unmapped = 0;

	if (!IS_ALIGNED(iova, PAGE_SIZE) || !IS_ALIGNED(total, PAGE_SIZE))
		return 0;

	while (unmapped < npages) {
		if (!xa_erase(&fake_dom->mappings, iova_pfn + unmapped))
			break;
		unmapped++;
	}

	return unmapped << PAGE_SHIFT;
}

static phys_addr_t fake_domain_iova_to_phys(struct iommu_domain *domain,
					    dma_addr_t iova)
{
	struct fake_iommu_domain *fake_dom = to_fake_domain(domain);
	void *entry;

	entry = xa_load(&fake_dom->mappings, iova >> PAGE_SHIFT);
	if (!entry || !xa_is_value(entry))
		return 0;

	return ((phys_addr_t)xa_to_value(entry) << PAGE_SHIFT) |
	       (iova & ~PAGE_MASK);
}

static const struct iommu_domain_ops fake_paging_domain_ops = {
	.attach_dev = fake_domain_attach,
	.free = fake_domain_free_paging,
	.map_pages = fake_domain_map_pages,
	.unmap_pages = fake_domain_unmap_pages,
	.iova_to_phys = fake_domain_iova_to_phys,
};

static struct iommu_domain *fake_domain_alloc_paging_common(void)
{
	struct fake_iommu_domain *fake_dom;

	fake_dom = kzalloc(sizeof(*fake_dom), GFP_KERNEL);
	if (!fake_dom)
		return ERR_PTR(-ENOMEM);

	fake_dom->domain.type = IOMMU_DOMAIN_UNMANAGED;
	fake_dom->domain.ops = &fake_paging_domain_ops;
	fake_dom->domain.pgsize_bitmap = PAGE_SIZE;
	fake_dom->domain.geometry.aperture_start = 0;
	fake_dom->domain.geometry.aperture_end = ~0UL;
	fake_dom->domain.geometry.force_aperture = true;
	xa_init(&fake_dom->mappings);

	return &fake_dom->domain;
}

#if PCI_SIM_IOMMU_HAS_DOMAIN_ALLOC_PAGING_FLAGS
static struct iommu_domain *
fake_domain_alloc_paging_flags(struct device *dev, u32 flags,
			       const struct iommu_user_data *user_data)
{
	if (flags & ~IOMMU_HWPT_ALLOC_PASID)
		return ERR_PTR(-EOPNOTSUPP);
	if (user_data)
		return ERR_PTR(-EOPNOTSUPP);

	return fake_domain_alloc_paging_common();
}
#else
static struct iommu_domain *fake_domain_alloc_paging(struct device *dev)
{
	return fake_domain_alloc_paging_common();
}
#endif

static bool fake_iommu_capable(struct device *dev, enum iommu_cap cap)
{
	switch (cap) {
	case IOMMU_CAP_CACHE_COHERENCY:
		return true;
	default:
		return false;
	}
}

static struct iommu_device *fake_iommu_probe_device(struct device *dev)
{
	struct fake_pci_host *host;
	struct pci_dev *pdev;
	bool found = false;
	int domain;

	if (!dev_is_pci(dev))
		return ERR_PTR(-ENODEV);

	pdev = to_pci_dev(dev);
	domain = pci_domain_nr(pdev->bus);

	mutex_lock(&fake_hosts_lock);
	list_for_each_entry(host, &fake_hosts, list) {
		if (domain == host->domain_nr) {
			found = true;
			break;
		}
	}
	mutex_unlock(&fake_hosts_lock);

	if (!found)
		return ERR_PTR(-ENODEV);

	dev_info(dev, "fake_iommu: probed device %04x:%02x:%02x.%d\n",
		 pci_domain_nr(pdev->bus), pdev->bus->number,
		 PCI_SLOT(pdev->devfn), PCI_FUNC(pdev->devfn));

	return &fake_iommu_dev;
}

static void fake_iommu_release_device(struct device *dev)
{
	dev_dbg(dev, "fake_iommu: released device\n");
}

static struct iommu_group *fake_iommu_device_group(struct device *dev)
{
	return generic_device_group(dev);
}

const struct iommu_ops fake_iommu_ops = {
	.owner = THIS_MODULE,
	.default_domain = &fake_blocking_domain,
	.blocked_domain = &fake_blocking_domain,
	.capable = fake_iommu_capable,
	.probe_device = fake_iommu_probe_device,
	.release_device = fake_iommu_release_device,
	.device_group = fake_iommu_device_group,
#if PCI_SIM_IOMMU_HAS_DOMAIN_ALLOC_PAGING_FLAGS
	.domain_alloc_paging_flags = fake_domain_alloc_paging_flags,
#else
	.domain_alloc_paging = fake_domain_alloc_paging,
#endif
};
