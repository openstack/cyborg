// SPDX-License-Identifier: GPL-2.0
/*
 * Fake PCI SR-IOV VFIO test fixture -- module lifecycle and host bridge setup
 *
 * This file owns the module parameters, the global host list, the PCI host
 * bridge probe/remove lifecycle, and the module init/exit entry points.
 * It coordinates the other subsystems (iommu, cfg, uart, vfio) by calling
 * their registration helpers in the correct order.
 */

#include "fake_pci_sriov.h"

/* Module parameters */

bool vf_serial_class;
module_param(vf_serial_class, bool, 0644);
MODULE_PARM_DESC(
	vf_serial_class,
	"Expose host-visible VFs as PCI serial/16550 class devices instead of vendor-specific");

bool vfio_guest_8250_compat = true;
module_param(vfio_guest_8250_compat, bool, 0644);
MODULE_PARM_DESC(
	vfio_guest_8250_compat,
	"Overlay VFIO guest config space with an 8250_pci-compatible SGI IOC3 serial identity");

bool vfio_uart_trace;
module_param(vfio_uart_trace, bool, 0644);
MODULE_PARM_DESC(vfio_uart_trace, "Trace VFIO BAR0 UART register accesses");

static int fake_intx_irq;
module_param(fake_intx_irq, int, 0644);
MODULE_PARM_DESC(
	fake_intx_irq,
	"Optional host IRQ number to report for fake PCI INTx routing (0 disables)");

static unsigned int num_pfs = 1;
module_param(num_pfs, uint, 0444);
MODULE_PARM_DESC(num_pfs, "Number of fake SR-IOV PFs to create");

static unsigned long mem_base;
module_param(mem_base, ulong, 0444);
MODULE_PARM_DESC(
	mem_base,
	"Fixed fake PCI MMIO window base address (0 chooses automatically)");

unsigned long mem_stride = FAKE_PCI_MEM_STRIDE;
module_param(mem_stride, ulong, 0444);
MODULE_PARM_DESC(mem_stride,
		 "Size and alignment of each fake PCI host MMIO window");

/* Global host list (also used by cfg.c and iommu.c) */

LIST_HEAD(fake_hosts);
DEFINE_MUTEX(fake_hosts_lock); /* Protects fake_hosts. */

/* PCI host bridge helpers */

static void *fake_pci_host_sysdata(struct fake_pci_host *host)
{
#ifdef CONFIG_X86
	return &host->sysdata;
#elif defined(CONFIG_ACPI)
	return &host->sysdata;
#else
	return NULL;
#endif
}

static void fake_pci_host_init_sysdata(struct fake_pci_host *host)
{
#ifdef CONFIG_X86
	host->sysdata.domain = host->domain_nr;
	host->sysdata.node = NUMA_NO_NODE;
#elif defined(CONFIG_ACPI)
	host->sysdata.priv = host;
#endif
}

static void fake_pci_release_host_bridge(struct pci_host_bridge *bridge)
{
	pr_info("fake_pci: releasing host bridge\n");
}

static int fake_pci_map_irq(const struct pci_dev *dev, u8 slot, u8 pin)
{
	return fake_intx_irq ?: -1;
}

static void fake_pci_host_release_mem_resource(struct fake_pci_host *host)
{
	if (!host->mem_resource_registered)
		return;

	release_resource(&host->mem_resource);
	host->mem_resource_registered = false;
}

static int fake_pci_alloc_mem_resource(struct fake_pci_host *host,
				       resource_size_t stride)
{
	static const struct {
		resource_size_t start;
		resource_size_t end;
		const char *name;
	} regions[] = {
		{ FAKE_PCI_MEM_BASE, U32_MAX, "32-bit high" },
		{ 0xc0000000ULL, 0xcfffffffULL, "32-bit mid" },
		{ 0x80000000ULL, 0xbfffffffULL, "32-bit low" },
#ifdef CONFIG_64BIT
		{ FAKE_PCI_MEM_64_BASE, (resource_size_t)-1, "64-bit" },
#endif
	};
	int i, ret = -EBUSY;

	for (i = 0; i < ARRAY_SIZE(regions); i++) {
		host->mem_resource.start = 0;
		host->mem_resource.end = 0;
		host->mem_resource.flags = IORESOURCE_MEM;
		if (regions[i].start > U32_MAX)
			host->mem_resource.flags |= IORESOURCE_MEM_64;

		ret = allocate_resource(&iomem_resource, &host->mem_resource,
					stride, regions[i].start,
					regions[i].end, stride, NULL, NULL);
		if (!ret) {
			host->mem_resource_registered = true;
			pr_info("fake_pci: allocated %s MMIO window [%#llx-%#llx]\n",
				regions[i].name,
				(unsigned long long)host->mem_resource.start,
				(unsigned long long)host->mem_resource.end);
			return 0;
		}

		pr_warn("fake_pci: failed to allocate %s %#llx-byte MMIO window: %d\n",
			regions[i].name, (unsigned long long)stride, ret);
	}

	return ret;
}

static int fake_pci_host_init_mem_resource(struct fake_pci_host *host,
					   unsigned int index)
{
	resource_size_t max_addr = (resource_size_t)-1;
	resource_size_t mem_start;
	resource_size_t stride = mem_stride;
	int ret;

	if (stride < FAKE_PCI_MEM_MIN_SIZE) {
		pr_err("fake_pci: mem_stride must be at least %#llx\n",
		       (unsigned long long)FAKE_PCI_MEM_MIN_SIZE);
		return -EINVAL;
	}

	host->mem_resource.flags = IORESOURCE_MEM;
	host->mem_resource.name = "fake_pci_mem";

	if (mem_base) {
		mem_start = (resource_size_t)mem_base;
		if ((unsigned long)mem_start != mem_base ||
		    index >= (max_addr - mem_start + 1) / stride) {
			pr_err("fake_pci: fixed MMIO window exceeds resource space\n");
			return -EINVAL;
		}

		mem_start += index * stride;
		host->mem_resource.start = mem_start;
		host->mem_resource.end = mem_start + stride - 1;
		if (mem_start > U32_MAX)
			host->mem_resource.flags |= IORESOURCE_MEM_64;
		return 0;
	}

	ret = fake_pci_alloc_mem_resource(host, stride);
	if (ret)
		pr_err("fake_pci: failed to allocate any MMIO window: %d\n",
		       ret);

	return ret;
}

static int fake_pci_host_probe(struct fake_pci_host *host, unsigned int index)
{
	struct pci_host_bridge *bridge;
	int err;

	mutex_init(&host->lock);

	host->domain_nr = index + 1;
	fake_pci_host_init_sysdata(host);

	host->bus_resource.start = 0;
	host->bus_resource.end = 0;
	host->bus_resource.flags = IORESOURCE_BUS;
	host->bus_resource.name = "fake_pci_bus";

	err = fake_pci_host_init_mem_resource(host, index);
	if (err)
		goto err_mutex;

	init_pf_config_space(&host->pf);

	bridge = pci_alloc_host_bridge(0);
	if (!bridge) {
		err = -ENOMEM;
		goto err_mem;
	}

	host->bridge = bridge;
	bridge->sysdata = fake_pci_host_sysdata(host);
	bridge->ops = &fake_pci_ops;
	bridge->map_irq = fake_pci_map_irq;
	bridge->busnr = 0;
	bridge->dev.parent = &host->pdev->dev;
	bridge->domain_nr = host->domain_nr;

	pci_set_host_bridge_release(bridge, fake_pci_release_host_bridge, NULL);

	pci_add_resource(&bridge->windows, &host->bus_resource);
	pci_add_resource(&bridge->windows, &host->mem_resource);

	mutex_lock(&fake_hosts_lock);
	list_add_tail(&host->list, &fake_hosts);
	mutex_unlock(&fake_hosts_lock);

	err = pci_host_probe(bridge);
	if (err) {
		pr_err("fake_pci: pci_host_probe failed for domain %04x: %d\n",
		       host->domain_nr, err);
		goto err_del_host;
	}

	pr_info("fake_pci: Host bridge created on domain %04x\n",
		host->domain_nr);

	return 0;

err_del_host:
	mutex_lock(&fake_hosts_lock);
	list_del(&host->list);
	mutex_unlock(&fake_hosts_lock);
	pci_free_host_bridge(bridge);
err_mem:
	fake_pci_host_release_mem_resource(host);
err_mutex:
	mutex_destroy(&host->lock);
	return err;
}

static void fake_pci_host_remove(struct fake_pci_host *host)
{
	struct platform_device *pdev;

	if (!host)
		return;

	if (host->bridge && host->bridge->bus) {
		pci_lock_rescan_remove();
		pci_stop_root_bus(host->bridge->bus);
		pci_remove_root_bus(host->bridge->bus);
		pci_unlock_rescan_remove();
	}

	mutex_lock(&fake_hosts_lock);
	list_del_init(&host->list);
	mutex_unlock(&fake_hosts_lock);

	fake_pci_host_release_mem_resource(host);

	pdev = host->pdev;
	mutex_destroy(&host->lock);
	kfree(host);
	if (pdev)
		platform_device_unregister(pdev);
}

static void fake_pci_remove_all_hosts(void)
{
	struct fake_pci_host *host, *tmp;

	list_for_each_entry_safe_reverse(host, tmp, &fake_hosts, list)
		fake_pci_host_remove(host);
}

/* Module init / exit */

static int __init fake_pci_sriov_init(void)
{
	struct platform_device_info pdevinfo = {
		.name = "fake-pci-iommu",
		.id = PLATFORM_DEVID_AUTO,
	};
	struct fake_pci_host *host;
	unsigned int i;
	int err;

	pr_info("fake_pci: Initializing fake PCI SR-IOV driver\n");

	if (!num_pfs || num_pfs > FAKE_PCI_MAX_HOSTS) {
		pr_err("fake_pci: num_pfs must be between 1 and %u\n",
		       FAKE_PCI_MAX_HOSTS);
		return -EINVAL;
	}

	fake_iommu_pdev = platform_device_register_full(&pdevinfo);
	if (IS_ERR(fake_iommu_pdev)) {
		err = PTR_ERR(fake_iommu_pdev);
		pr_err("fake_pci: Failed to register IOMMU platform device: %d\n",
		       err);
		return err;
	}

	err = iommu_device_sysfs_add(&fake_iommu_dev, &fake_iommu_pdev->dev,
				     NULL, "fake-pci-iommu");
	if (err) {
		pr_err("fake_pci: Failed to add IOMMU sysfs: %d\n", err);
		goto err_platform_dev;
	}

	err = iommu_device_register(&fake_iommu_dev, &fake_iommu_ops,
				    &fake_iommu_pdev->dev);
	if (err) {
		pr_err("fake_pci: Failed to register IOMMU: %d\n", err);
		goto err_iommu_sysfs;
	}

	pr_info("fake_pci: Software IOMMU registered\n");

	err = pci_sim_tty_register_driver();
	if (err) {
		pr_err("fake_pci: Failed to register TTY driver: %d\n", err);
		goto err_iommu;
	}

	err = pci_register_driver(&pci_sim_vfio_driver);
	if (err) {
		pr_err("fake_pci: Failed to register VFIO UART driver: %d\n",
		       err);
		goto err_tty;
	}

	err = pci_register_driver(&pci_sim_vf_driver);
	if (err) {
		pr_err("fake_pci: Failed to register VF loopback driver: %d\n",
		       err);
		goto err_vfio_driver;
	}

	err = pci_register_driver(&fake_pci_pf_driver);
	if (err) {
		pr_err("fake_pci: Failed to register PF driver: %d\n", err);
		goto err_vf_driver;
	}

	pdevinfo.name = "fake-pci-host";

	for (i = 0; i < num_pfs; i++) {
		host = kzalloc(sizeof(*host), GFP_KERNEL);
		if (!host) {
			err = -ENOMEM;
			goto err_hosts;
		}
		INIT_LIST_HEAD(&host->list);

		host->pdev = platform_device_register_full(&pdevinfo);
		if (IS_ERR(host->pdev)) {
			err = PTR_ERR(host->pdev);
			pr_err("fake_pci: Failed to register PCI host platform device %u: %d\n",
			       i, err);
			kfree(host);
			goto err_hosts;
		}

		err = fake_pci_host_probe(host, i);
		if (err) {
			platform_device_unregister(host->pdev);
			kfree(host);
			goto err_hosts;
		}
	}

	pr_info("fake_pci: Module loaded successfully with %u PF(s)\n",
		num_pfs);
	pr_info("fake_pci: Use 'echo N > /sys/bus/pci/devices/.../sriov_numvfs' to enable VFs\n");

	return 0;

err_hosts:
	fake_pci_remove_all_hosts();
	pci_unregister_driver(&fake_pci_pf_driver);
err_vf_driver:
	pci_unregister_driver(&pci_sim_vf_driver);
err_vfio_driver:
	pci_unregister_driver(&pci_sim_vfio_driver);
err_tty:
	pci_sim_tty_unregister_driver();
err_iommu:
	iommu_device_unregister(&fake_iommu_dev);
err_iommu_sysfs:
	iommu_device_sysfs_remove(&fake_iommu_dev);
err_platform_dev:
	platform_device_unregister(fake_iommu_pdev);
	return err;
}

static void __exit fake_pci_sriov_exit(void)
{
	pr_info("fake_pci: Unloading module\n");

	fake_pci_remove_all_hosts();

	pci_unregister_driver(&fake_pci_pf_driver);
	pci_unregister_driver(&pci_sim_vf_driver);
	pci_unregister_driver(&pci_sim_vfio_driver);
	pci_sim_tty_unregister_driver();

	iommu_device_unregister(&fake_iommu_dev);
	iommu_device_sysfs_remove(&fake_iommu_dev);
	platform_device_unregister(fake_iommu_pdev);

	pr_info("fake_pci: Module unloaded\n");
}

module_init(fake_pci_sriov_init);
module_exit(fake_pci_sriov_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("OpenStack Contributors");
MODULE_DESCRIPTION(
	"Fake PCI Host Controller with Software IOMMU for SR-IOV Testing");
