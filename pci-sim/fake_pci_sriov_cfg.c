// SPDX-License-Identifier: GPL-2.0
/*
 * Fake PCI SR-IOV VFIO test fixture -- PCI config space and SR-IOV management
 *
 * Implements the fake pci_ops config-space read/write paths, PCI capability
 * initialisation (PCIe, SR-IOV), and the PF driver that owns sriov_configure.
 */

#include "fake_pci_sriov.h"

/* =========================================================================
 * Config-space byte helpers
 * ========================================================================= */

static u16 fake_cfg_read16(const u8 *config, int where)
{
	return get_unaligned_le16(config + where);
}

static u32 fake_cfg_read32(const u8 *config, int where)
{
	return get_unaligned_le32(config + where);
}

static void fake_cfg_write16(u8 *config, int where, u16 val)
{
	put_unaligned_le16(val, config + where);
}

static void fake_cfg_write32(u8 *config, int where, u32 val)
{
	put_unaligned_le32(val, config + where);
}

static int fake_cfg_read(const u8 *config, int where, int size, u32 *val)
{
	switch (size) {
	case 1:
		*val = config[where];
		return PCIBIOS_SUCCESSFUL;
	case 2:
		*val = fake_cfg_read16(config, where);
		return PCIBIOS_SUCCESSFUL;
	case 4:
		*val = fake_cfg_read32(config, where);
		return PCIBIOS_SUCCESSFUL;
	default:
		*val = ~0;
		return PCIBIOS_BAD_REGISTER_NUMBER;
	}
}

static int fake_cfg_write(u8 *config, int where, int size, u32 val)
{
	switch (size) {
	case 1:
		config[where] = val;
		return PCIBIOS_SUCCESSFUL;
	case 2:
		fake_cfg_write16(config, where, val);
		return PCIBIOS_SUCCESSFUL;
	case 4:
		fake_cfg_write32(config, where, val);
		return PCIBIOS_SUCCESSFUL;
	default:
		return PCIBIOS_BAD_REGISTER_NUMBER;
	}
}

/* =========================================================================
 * Host-lookup helpers (used by iommu.c and pci_ops below)
 * ========================================================================= */

struct fake_pci_host *fake_pci_host_from_domain(int domain)
{
	struct fake_pci_host *host;

	lockdep_assert_held(&fake_hosts_lock);

	list_for_each_entry(host, &fake_hosts, list) {
		if (domain == host->domain_nr)
			return host;
	}

	return NULL;
}

/* =========================================================================
 * PCI capability initialisation
 * ========================================================================= */

static void fake_pci_set_class(u8 *config, u32 class)
{
	config[PCI_CLASS_PROG] = class & 0xff;
	config[PCI_CLASS_DEVICE] = (class >> 8) & 0xff;
	config[PCI_CLASS_DEVICE + 1] = (class >> 16) & 0xff;
}

static void init_pcie_capability(u8 *config, bool is_pf)
{
	u8 *cap = &config[PCIE_CAP_OFFSET];
	u32 link_cap;
	u16 exp_flags, link_status;

	cap[PCI_CAP_LIST_ID] = PCI_CAP_ID_EXP;
	cap[PCI_CAP_LIST_NEXT] = 0;

	exp_flags = 2 | (PCI_EXP_TYPE_ENDPOINT << 4);
	fake_cfg_write16(cap, PCI_EXP_FLAGS, exp_flags);

	fake_cfg_write32(cap, PCI_EXP_DEVCAP, PCI_EXP_DEVCAP_FLR);
	fake_cfg_write16(cap, PCI_EXP_DEVCTL, 0);
	fake_cfg_write16(cap, PCI_EXP_DEVSTA, 0);

	link_cap = PCI_EXP_LNKCAP_SLS_2_5GB | (1 << 4);
	fake_cfg_write32(cap, PCI_EXP_LNKCAP, link_cap);

	link_status = PCI_EXP_LNKSTA_CLS_2_5GB | PCI_EXP_LNKSTA_NLW_X1;
	fake_cfg_write16(cap, PCI_EXP_LNKSTA, link_status);
}

static void init_sriov_capability(u8 *config)
{
	u8 *cap = &config[SRIOV_CAP_OFFSET];

	fake_cfg_write16(cap, 0, PCI_EXT_CAP_ID_SRIOV);
	fake_cfg_write16(cap, 2, 0);
	fake_cfg_write32(cap, PCI_SRIOV_CAP, 0);
	fake_cfg_write16(cap, PCI_SRIOV_CTRL, 0);
	fake_cfg_write16(cap, PCI_SRIOV_STATUS, 0);
	fake_cfg_write16(cap, PCI_SRIOV_INITIAL_VF, MAX_VFS);
	fake_cfg_write16(cap, PCI_SRIOV_TOTAL_VF, MAX_VFS);
	fake_cfg_write16(cap, PCI_SRIOV_NUM_VF, 0);
	fake_cfg_write16(cap, PCI_SRIOV_FUNC_LINK, 0);
	fake_cfg_write16(cap, PCI_SRIOV_VF_OFFSET, 1);
	fake_cfg_write16(cap, PCI_SRIOV_VF_STRIDE, 1);
	fake_cfg_write16(cap, PCI_SRIOV_VF_DID, FAKE_PCI_VF_DEVICE_ID);
	fake_cfg_write32(cap, PCI_SRIOV_SUP_PGSIZE, 1);
	fake_cfg_write32(cap, PCI_SRIOV_SYS_PGSIZE, 1);
	fake_cfg_write32(cap, PCI_SRIOV_BAR, FAKE_PCI_BAR_FLAGS);
	fake_cfg_write32(cap, PCI_SRIOV_BAR + 4, 0);
}

static int fake_pci_write_bar(u8 *config, int where, u32 val, int base)
{
	int bar_num = (where - base) / 4;

	if (bar_num == 0) {
		if (val == 0xffffffff) {
			fake_cfg_write32(config, where,
					 ~(BAR0_SIZE - 1) | FAKE_PCI_BAR_FLAGS);
		} else {
			fake_cfg_write32(config, where,
					 (val & ~(BAR0_SIZE - 1)) |
					 FAKE_PCI_BAR_FLAGS);
		}
		return PCIBIOS_SUCCESSFUL;
	}

	if (bar_num == 1) {
		fake_cfg_write32(config, where,
				 val == 0xffffffff ? 0xffffffff : val);
		return PCIBIOS_SUCCESSFUL;
	}

	fake_cfg_write32(config, where, 0);
	return PCIBIOS_SUCCESSFUL;
}

void init_pf_config_space(struct fake_pci_device *dev)
{
	u8 *config = dev->config_space;

	memset(config, 0, sizeof(dev->config_space));
	dev->present = true;
	dev->is_vf = false;

	fake_cfg_write16(config, PCI_VENDOR_ID, FAKE_PCI_VENDOR_ID);
	fake_cfg_write16(config, PCI_DEVICE_ID, FAKE_PCI_PF_DEVICE_ID);
	fake_cfg_write16(config, PCI_COMMAND,
			 PCI_COMMAND_IO | PCI_COMMAND_MEMORY | PCI_COMMAND_MASTER);
	fake_cfg_write16(config, PCI_STATUS, PCI_STATUS_CAP_LIST);

	config[PCI_REVISION_ID] = 0x01;
	fake_pci_set_class(config, FAKE_PCI_VENDOR_CLASS);
	config[PCI_CACHE_LINE_SIZE] = 64 / 4;
	config[PCI_HEADER_TYPE] = PCI_HEADER_TYPE_NORMAL | PCI_HEADER_TYPE_MFD;

	fake_cfg_write32(config, PCI_BASE_ADDRESS_0, FAKE_PCI_BAR_FLAGS);
	fake_cfg_write32(config, PCI_BASE_ADDRESS_1, 0);
	fake_cfg_write16(config, PCI_SUBSYSTEM_VENDOR_ID, FAKE_PCI_SUBSYS_VENDOR);
	fake_cfg_write16(config, PCI_SUBSYSTEM_ID, FAKE_PCI_SUBSYS_ID);

	config[PCI_CAPABILITY_LIST] = PCIE_CAP_OFFSET;
	config[PCI_INTERRUPT_LINE] = 0;
	config[PCI_INTERRUPT_PIN] = 1;

	init_pcie_capability(config, true);
	init_sriov_capability(config);
}

static void init_vf_config_space(struct fake_pci_device *dev, int vf_index)
{
	u8 *config = dev->config_space;

	memset(config, 0, sizeof(dev->config_space));
	dev->present = true;
	dev->is_vf = true;
	dev->vf_index = vf_index;

	fake_cfg_write16(config, PCI_VENDOR_ID, FAKE_PCI_VENDOR_ID);
	fake_cfg_write16(config, PCI_DEVICE_ID, FAKE_PCI_VF_DEVICE_ID);
	fake_cfg_write16(config, PCI_COMMAND,
			 PCI_COMMAND_IO | PCI_COMMAND_MEMORY | PCI_COMMAND_MASTER);
	fake_cfg_write16(config, PCI_STATUS, PCI_STATUS_CAP_LIST);

	config[PCI_REVISION_ID] = 0x01;
	fake_pci_set_class(config, vf_serial_class ? FAKE_PCI_SERIAL_CLASS :
			   FAKE_PCI_VENDOR_CLASS);
	config[PCI_CACHE_LINE_SIZE] = 64 / 4;
	config[PCI_HEADER_TYPE] = PCI_HEADER_TYPE_NORMAL;

	fake_cfg_write32(config, PCI_BASE_ADDRESS_0, FAKE_PCI_BAR_FLAGS);
	fake_cfg_write32(config, PCI_BASE_ADDRESS_1, 0);
	fake_cfg_write16(config, PCI_SUBSYSTEM_VENDOR_ID, FAKE_PCI_SUBSYS_VENDOR);
	fake_cfg_write16(config, PCI_SUBSYSTEM_ID, FAKE_PCI_SUBSYS_ID);

	config[PCI_CAPABILITY_LIST] = PCIE_CAP_OFFSET;

	init_pcie_capability(config, false);
}

/* =========================================================================
 * pci_ops: config-space read/write
 * ========================================================================= */

static struct fake_pci_device *get_fake_device(struct fake_pci_host *host,
					       unsigned int devfn)
{
	int slot = PCI_SLOT(devfn);
	int func = PCI_FUNC(devfn);

	if (slot != 0)
		return NULL;

	if (func == 0)
		return &host->pf;

	if (func >= 1 && func <= MAX_VFS) {
		int vf_idx = func - 1;

		if (vf_idx < host->num_vfs_enabled)
			return &host->vfs[vf_idx];
	}

	return NULL;
}

static int fake_pci_read_config(struct pci_bus *bus, unsigned int devfn,
				int where, int size, u32 *val)
{
	struct fake_pci_host *host;
	struct fake_pci_device *dev;
	int ret;

	if (bus->number != 0) {
		*val = ~0;
		return PCIBIOS_DEVICE_NOT_FOUND;
	}

	mutex_lock(&fake_hosts_lock);
	host = fake_pci_host_from_domain(pci_domain_nr(bus));
	if (!host) {
		mutex_unlock(&fake_hosts_lock);
		*val = ~0;
		return PCIBIOS_DEVICE_NOT_FOUND;
	}

	dev = get_fake_device(host, devfn);
	if (!dev || !dev->present) {
		mutex_unlock(&fake_hosts_lock);
		*val = ~0;
		return PCIBIOS_DEVICE_NOT_FOUND;
	}

	if (where + size > sizeof(dev->config_space)) {
		mutex_unlock(&fake_hosts_lock);
		*val = ~0;
		return PCIBIOS_BAD_REGISTER_NUMBER;
	}

	ret = fake_cfg_read(dev->config_space, where, size, val);
	mutex_unlock(&fake_hosts_lock);
	return ret;
}

static void handle_sriov_numvfs_write(struct fake_pci_host *host, u16 num_vfs);

static bool fake_pci_is_sriov_cfg(int where)
{
	return where >= SRIOV_CAP_OFFSET &&
	       where < SRIOV_CAP_OFFSET + PCI_SRIOV_BAR +
		       PCI_SRIOV_NUM_BARS * 4;
}

static int fake_pci_write_config(struct pci_bus *bus, unsigned int devfn,
				 int where, int size, u32 val)
{
	struct fake_pci_host *host;
	struct fake_pci_device *dev;
	u8 *config;
	int ret;

	if (bus->number != 0)
		return PCIBIOS_DEVICE_NOT_FOUND;

	mutex_lock(&fake_hosts_lock);
	host = fake_pci_host_from_domain(pci_domain_nr(bus));
	if (!host) {
		ret = PCIBIOS_DEVICE_NOT_FOUND;
		goto out_unlock;
	}

	dev = get_fake_device(host, devfn);
	if (!dev || !dev->present) {
		ret = PCIBIOS_DEVICE_NOT_FOUND;
		goto out_unlock;
	}

	if (where + size > sizeof(dev->config_space)) {
		ret = PCIBIOS_BAD_REGISTER_NUMBER;
		goto out_unlock;
	}

	config = dev->config_space;

	if (size == 4 && where >= PCI_BASE_ADDRESS_0 &&
	    where < PCI_BASE_ADDRESS_5 + 4) {
		ret = fake_pci_write_bar(config, where, val, PCI_BASE_ADDRESS_0);
		goto out_unlock;
	}

	if (size == 4 && where == PCI_ROM_ADDRESS) {
		fake_cfg_write32(config, PCI_ROM_ADDRESS, 0);
		ret = PCIBIOS_SUCCESSFUL;
		goto out_unlock;
	}

	if (size == 4 && !dev->is_vf &&
	    where >= SRIOV_CAP_OFFSET + PCI_SRIOV_BAR &&
	    where < SRIOV_CAP_OFFSET + PCI_SRIOV_BAR +
		    PCI_SRIOV_NUM_BARS * 4) {
		ret = fake_pci_write_bar(config, where, val,
					 SRIOV_CAP_OFFSET + PCI_SRIOV_BAR);
		goto out_unlock;
	}

	if (!dev->is_vf && fake_pci_is_sriov_cfg(where)) {
		ret = fake_cfg_write(config, where, size, val);
		goto out_unlock;
	}

	switch (where) {
	case PCI_VENDOR_ID:
	case PCI_DEVICE_ID:
	case PCI_REVISION_ID:
	case PCI_CLASS_PROG:
	case PCI_CLASS_DEVICE:
	case PCI_HEADER_TYPE:
	case PCI_SUBSYSTEM_VENDOR_ID:
	case PCI_SUBSYSTEM_ID:
	case PCI_CAPABILITY_LIST:
		ret = PCIBIOS_SUCCESSFUL;
		goto out_unlock;
	}

	ret = fake_cfg_write(config, where, size, val);

out_unlock:
	mutex_unlock(&fake_hosts_lock);
	return ret;
}

struct pci_ops fake_pci_ops = {
	.read	= fake_pci_read_config,
	.write	= fake_pci_write_config,
};

/* =========================================================================
 * SR-IOV VF enable/disable
 * ========================================================================= */

static void handle_sriov_numvfs_write(struct fake_pci_host *host, u16 num_vfs)
{
	u8 *pf_config = host->pf.config_space;
	int i;

	mutex_lock(&host->lock);

	if (num_vfs > MAX_VFS)
		num_vfs = MAX_VFS;

	pr_info("fake_pci: Setting NumVFs from %d to %d\n",
		host->num_vfs_enabled, num_vfs);

	for (i = num_vfs; i < host->num_vfs_enabled; i++) {
		host->vfs[i].present = false;
		pr_info("fake_pci: Disabled VF%d\n", i);
	}

	for (i = host->num_vfs_enabled; i < num_vfs; i++) {
		init_vf_config_space(&host->vfs[i], i);
		pr_info("fake_pci: Enabled VF%d\n", i);
	}

	host->num_vfs_enabled = num_vfs;
	fake_cfg_write16(pf_config, SRIOV_CAP_OFFSET + PCI_SRIOV_NUM_VF, num_vfs);

	mutex_unlock(&host->lock);
}

/* =========================================================================
 * PF driver
 * ========================================================================= */

static struct fake_pci_host *fake_pci_host_from_pdev(struct pci_dev *pdev)
{
	struct fake_pci_host *host;

	mutex_lock(&fake_hosts_lock);
	host = fake_pci_host_from_domain(pci_domain_nr(pdev->bus));
	mutex_unlock(&fake_hosts_lock);

	return host;
}

static int fake_pci_pf_probe(struct pci_dev *pdev,
			     const struct pci_device_id *id)
{
	struct fake_pci_host *host = fake_pci_host_from_pdev(pdev);

	if (!host)
		return -ENODEV;

	pci_set_drvdata(pdev, host);
	pci_info(pdev, "fake_pci: PF probed\n");
	return 0;
}

static void fake_pci_pf_remove(struct pci_dev *pdev)
{
	struct fake_pci_host *host = pci_get_drvdata(pdev);

	if (pci_num_vf(pdev)) {
		pci_info(pdev, "fake_pci: disabling VFs before PF removal\n");
		pci_disable_sriov(pdev);
		if (host)
			handle_sriov_numvfs_write(host, 0);
	}

	pci_set_drvdata(pdev, NULL);
	pci_info(pdev, "fake_pci: PF removed\n");
}

static int fake_pci_sriov_configure(struct pci_dev *pdev, int num_vfs)
{
	struct fake_pci_host *host = pci_get_drvdata(pdev);
	int err;

	if (!host)
		return -ENODEV;

	if (num_vfs < 0 || num_vfs > MAX_VFS)
		return -EINVAL;

	if (!num_vfs) {
		pci_disable_sriov(pdev);
		handle_sriov_numvfs_write(host, 0);
		return 0;
	}

	if (host->num_vfs_enabled)
		return -EBUSY;

	handle_sriov_numvfs_write(host, num_vfs);

	err = pci_enable_sriov(pdev, num_vfs);
	if (err) {
		handle_sriov_numvfs_write(host, 0);
		return err;
	}

	return num_vfs;
}

static const struct pci_device_id fake_pci_pf_ids[] = {
	{ PCI_DEVICE(FAKE_PCI_VENDOR_ID, FAKE_PCI_PF_DEVICE_ID) },
	{ }
};
MODULE_DEVICE_TABLE(pci, fake_pci_pf_ids);

struct pci_driver fake_pci_pf_driver = {
	.name		= "fake_pci_sriov_pf",
	.id_table	= fake_pci_pf_ids,
	.probe		= fake_pci_pf_probe,
	.remove		= fake_pci_pf_remove,
	.sriov_configure = fake_pci_sriov_configure,
};
