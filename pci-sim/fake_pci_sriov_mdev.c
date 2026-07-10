// SPDX-License-Identifier: GPL-2.0
/*
 * Fake PCI SR-IOV VFIO test fixture -- mdev (mediated device) support
 *
 * Registers each fake PF as an mdev parent with two type groups, exposing
 * the standard /sys/class/mdev_bus/ sysfs tree that Cyborg's MdevBusManager
 * reads.  Each created mdev instance provides a minimal VFIO device with
 * an emulated PCI config space and a 16550 UART on BAR0.
 */

#include "fake_pci_sriov.h"

#if PCI_SIM_HAS_MDEV

#include <linux/vfio.h>

/* Per-type description strings */
static const char *const pci_sim_mdev_descriptions[] = {
	[PCI_SIM_MDEV_SMALL_IDX] =
		"PCI-SIM simulated small accelerator for testing",
	[PCI_SIM_MDEV_LARGE_IDX] =
		"PCI-SIM simulated large accelerator for testing",
};

static const char *const pci_sim_mdev_names[] = {
	[PCI_SIM_MDEV_SMALL_IDX] = "PCI-SIM Small Accelerator",
	[PCI_SIM_MDEV_LARGE_IDX] = "PCI-SIM Large Accelerator",
};

/* ---- mdev config space ------------------------------------------------- */

static void pci_sim_mdev_init_config(struct pci_sim_mdev_state *state)
{
	u8 *cfg = state->config;

	memset(cfg, 0, PCI_SIM_MDEV_CONFIG_SIZE);

	/* Vendor / Device */
	put_unaligned_le16(FAKE_PCI_VENDOR_ID, cfg + PCI_VENDOR_ID);
	put_unaligned_le16(FAKE_PCI_MDEV_DEVICE_ID, cfg + PCI_DEVICE_ID);

	/* Status: capabilities list not present */
	put_unaligned_le16(0, cfg + PCI_STATUS);

	/* Class: vendor-specific */
	cfg[PCI_REVISION_ID] = 0x01;
	cfg[PCI_CLASS_PROG] = 0x00;
	put_unaligned_le16(0xff00, cfg + PCI_CLASS_DEVICE);

	/* Header type 0 */
	cfg[PCI_HEADER_TYPE] = PCI_HEADER_TYPE_NORMAL;

	/* Subsystem IDs */
	put_unaligned_le16(FAKE_PCI_SUBSYS_VENDOR,
			   cfg + PCI_SUBSYSTEM_VENDOR_ID);
	put_unaligned_le16(FAKE_PCI_SUBSYS_ID, cfg + PCI_SUBSYSTEM_ID);

	/* BAR0: 4 KiB memory-mapped, 32-bit */
	put_unaligned_le32(PCI_BASE_ADDRESS_SPACE_MEMORY,
			   cfg + PCI_BASE_ADDRESS_0);
}

/* ---- VFIO device ops --------------------------------------------------- */

static int pci_sim_mdev_init_dev(struct vfio_device *vdev)
{
	return 0;
}

static void pci_sim_mdev_release_dev(struct vfio_device *vdev)
{
	struct pci_sim_mdev_state *state =
		container_of(vdev, struct pci_sim_mdev_state, vdev);

	mutex_destroy(&state->lock);
}

static int pci_sim_mdev_open_device(struct vfio_device *vdev)
{
	struct pci_sim_mdev_state *state =
		container_of(vdev, struct pci_sim_mdev_state, vdev);

	pci_sim_uart_reset(&state->uart);
	return 0;
}

static void pci_sim_mdev_close_device(struct vfio_device *vdev)
{
}

static ssize_t pci_sim_mdev_cfg_rw(struct pci_sim_mdev_state *state,
				   char __user *buf, size_t count, loff_t pos,
				   bool iswrite)
{
	size_t done;

	if (pos >= PCI_SIM_MDEV_CONFIG_SIZE)
		return -EINVAL;
	count = min_t(size_t, count, PCI_SIM_MDEV_CONFIG_SIZE - pos);

	mutex_lock(&state->lock);
	if (iswrite) {
		if (copy_from_user(state->config + pos, buf, count)) {
			mutex_unlock(&state->lock);
			return -EFAULT;
		}
		done = count;
	} else {
		if (copy_to_user(buf, state->config + pos, count)) {
			mutex_unlock(&state->lock);
			return -EFAULT;
		}
		done = count;
	}
	mutex_unlock(&state->lock);
	return done;
}

static ssize_t pci_sim_mdev_bar0_rw(struct pci_sim_mdev_state *state,
				    char __user *buf, size_t count, loff_t pos,
				    bool iswrite)
{
	size_t done;
	u8 reg, val;

	if (pos >= BAR0_SIZE)
		return -EINVAL;
	count = min_t(size_t, count, BAR0_SIZE - pos);

	mutex_lock(&state->lock);
	for (done = 0; done < count; done++) {
		if (iswrite) {
			if (copy_from_user(&val, buf + done, 1)) {
				mutex_unlock(&state->lock);
				return done ?: -EFAULT;
			}
			if (pos + done < 8) {
				reg = pos + done;
				pci_sim_uart_write_reg(&state->uart, reg, val);
			}
		} else {
			if (pos + done < 8) {
				reg = pos + done;
				val = pci_sim_uart_read_reg(&state->uart, reg);
			} else {
				val = 0xff;
			}
			if (copy_to_user(buf + done, &val, 1)) {
				mutex_unlock(&state->lock);
				return done ?: -EFAULT;
			}
		}
	}
	mutex_unlock(&state->lock);
	return done;
}

static ssize_t pci_sim_mdev_read(struct vfio_device *vdev, char __user *buf,
				 size_t count, loff_t *ppos)
{
	struct pci_sim_mdev_state *state =
		container_of(vdev, struct pci_sim_mdev_state, vdev);
	unsigned int index = VFIO_PCI_OFFSET_TO_INDEX(*ppos);
	loff_t pos = *ppos & VFIO_PCI_OFFSET_MASK;
	ssize_t ret;

	if (!count)
		return 0;

	switch (index) {
	case VFIO_PCI_CONFIG_REGION_INDEX:
		ret = pci_sim_mdev_cfg_rw(state, buf, count, pos, false);
		break;
	case VFIO_PCI_BAR0_REGION_INDEX:
		ret = pci_sim_mdev_bar0_rw(state, buf, count, pos, false);
		break;
	default:
		ret = -EINVAL;
		break;
	}

	if (ret > 0)
		*ppos += ret;
	return ret;
}

static ssize_t pci_sim_mdev_write(struct vfio_device *vdev,
				  const char __user *buf, size_t count,
				  loff_t *ppos)
{
	struct pci_sim_mdev_state *state =
		container_of(vdev, struct pci_sim_mdev_state, vdev);
	unsigned int index = VFIO_PCI_OFFSET_TO_INDEX(*ppos);
	loff_t pos = *ppos & VFIO_PCI_OFFSET_MASK;
	ssize_t ret;

	if (!count)
		return 0;

	switch (index) {
	case VFIO_PCI_CONFIG_REGION_INDEX:
		ret = pci_sim_mdev_cfg_rw(state, (char __user *)buf, count, pos,
					  true);
		break;
	case VFIO_PCI_BAR0_REGION_INDEX:
		ret = pci_sim_mdev_bar0_rw(state, (char __user *)buf, count,
					   pos, true);
		break;
	default:
		ret = -EINVAL;
		break;
	}

	if (ret > 0)
		*ppos += ret;
	return ret;
}

static int pci_sim_mdev_fill_region_info(struct vfio_device *vdev,
					 struct vfio_region_info *info)
{
	switch (info->index) {
	case VFIO_PCI_CONFIG_REGION_INDEX:
		info->offset = VFIO_PCI_INDEX_TO_OFFSET(info->index);
		info->size = PCI_SIM_MDEV_CONFIG_SIZE;
		info->flags = VFIO_REGION_INFO_FLAG_READ |
			      VFIO_REGION_INFO_FLAG_WRITE;
		return 0;
	case VFIO_PCI_BAR0_REGION_INDEX:
		info->offset = VFIO_PCI_INDEX_TO_OFFSET(info->index);
		info->size = BAR0_SIZE;
		info->flags = VFIO_REGION_INFO_FLAG_READ |
			      VFIO_REGION_INFO_FLAG_WRITE;
		return 0;
	default:
		if (info->index < VFIO_PCI_NUM_REGIONS) {
			info->offset = VFIO_PCI_INDEX_TO_OFFSET(info->index);
			info->size = 0;
			info->flags = 0;
			return 0;
		}
		return -EINVAL;
	}
}

static long pci_sim_mdev_ioctl(struct vfio_device *vdev, unsigned int cmd,
			       unsigned long arg)
{
	void __user *uarg = (void __user *)arg;

	switch (cmd) {
	case VFIO_DEVICE_GET_INFO: {
		struct vfio_device_info info;

		if (copy_from_user(&info, uarg, sizeof(info)))
			return -EFAULT;
		if (info.argsz < sizeof(info))
			return -EINVAL;

		info.flags = VFIO_DEVICE_FLAGS_PCI | VFIO_DEVICE_FLAGS_RESET;
		info.num_regions = VFIO_PCI_NUM_REGIONS;
		info.num_irqs = VFIO_PCI_NUM_IRQS;

		if (copy_to_user(uarg, &info, sizeof(info)))
			return -EFAULT;
		return 0;
	}
	case VFIO_DEVICE_GET_REGION_INFO: {
		struct vfio_region_info info;
		int ret;

		if (copy_from_user(&info, uarg, sizeof(info)))
			return -EFAULT;
		if (info.argsz < sizeof(info))
			return -EINVAL;

		ret = pci_sim_mdev_fill_region_info(vdev, &info);
		if (ret)
			return ret;

		info.cap_offset = 0;
		if (copy_to_user(uarg, &info, sizeof(info)))
			return -EFAULT;
		return 0;
	}
	case VFIO_DEVICE_GET_IRQ_INFO: {
		struct vfio_irq_info info;

		if (copy_from_user(&info, uarg, sizeof(info)))
			return -EFAULT;
		if (info.argsz < sizeof(info))
			return -EINVAL;
		if (info.index >= VFIO_PCI_NUM_IRQS)
			return -EINVAL;

		info.flags = 0;
		info.count = 0;

		if (copy_to_user(uarg, &info, sizeof(info)))
			return -EFAULT;
		return 0;
	}
	case VFIO_DEVICE_SET_IRQS:
		return 0;
	case VFIO_DEVICE_RESET: {
		struct pci_sim_mdev_state *state =
			container_of(vdev, struct pci_sim_mdev_state, vdev);

		pci_sim_uart_reset(&state->uart);
		return 0;
	}
	default:
		return -ENOTTY;
	}
}

static int pci_sim_mdev_mmap(struct vfio_device *vdev,
			     struct vm_area_struct *vma)
{
	return -EINVAL;
}

#if PCI_SIM_VFIO_HAS_GET_REGION_INFO_CAPS
static int pci_sim_mdev_get_region_info(struct vfio_device *vdev,
					struct vfio_region_info *info,
					struct vfio_info_cap *caps)
{
	return pci_sim_mdev_fill_region_info(vdev, info);
}
#endif

static const struct vfio_device_ops pci_sim_mdev_vfio_ops = {
	.name = "pci_sim_mdev",
	.init = pci_sim_mdev_init_dev,
	.release = pci_sim_mdev_release_dev,
	.open_device = pci_sim_mdev_open_device,
	.close_device = pci_sim_mdev_close_device,
	.ioctl = pci_sim_mdev_ioctl,
#if PCI_SIM_VFIO_HAS_GET_REGION_INFO_CAPS
	.get_region_info_caps = pci_sim_mdev_get_region_info,
#endif
	.read = pci_sim_mdev_read,
	.write = pci_sim_mdev_write,
	.mmap = pci_sim_mdev_mmap,
	.bind_iommufd = vfio_iommufd_emulated_bind,
	.unbind_iommufd = vfio_iommufd_emulated_unbind,
	.attach_ioas = vfio_iommufd_emulated_attach_ioas,
	.detach_ioas = vfio_iommufd_emulated_detach_ioas,
};

/* ---- mdev driver callbacks --------------------------------------------- */

static int pci_sim_mdev_probe(struct mdev_device *mdev)
{
	struct pci_sim_mdev_state *state;
	struct mdev_type *type = mdev->type;
	struct pci_sim_mdev_parent *mp;
	int type_idx, ret;

	mp = container_of(type->parent, struct pci_sim_mdev_parent, parent);

	/* Determine type index from embedded types array */
	for (type_idx = 0; type_idx < PCI_SIM_MDEV_NUM_TYPES; type_idx++) {
		if (&mp->types[type_idx] == type)
			break;
	}
	if (type_idx >= PCI_SIM_MDEV_NUM_TYPES)
		return -EINVAL;

	if (atomic_add_unless(&mp->avail[type_idx], -1, 0) == 0)
		return -ENOSPC;

	state = vfio_alloc_device(pci_sim_mdev_state, vdev, &mdev->dev,
				  &pci_sim_mdev_vfio_ops);
	if (IS_ERR(state)) {
		atomic_inc(&mp->avail[type_idx]);
		return PTR_ERR(state);
	}

	state->type_idx = type_idx;
	mutex_init(&state->lock);
	pci_sim_uart_init(&state->uart);
	pci_sim_mdev_init_config(state);

	ret = vfio_register_emulated_iommu_dev(&state->vdev);
	if (ret) {
		vfio_put_device(&state->vdev);
		atomic_inc(&mp->avail[type_idx]);
		return ret;
	}

	dev_set_drvdata(&mdev->dev, state);
	dev_info(&mdev->dev, "mdev instance created (type %d)\n", type_idx);
	return 0;
}

static void pci_sim_mdev_remove(struct mdev_device *mdev)
{
	struct pci_sim_mdev_state *state = dev_get_drvdata(&mdev->dev);
	struct mdev_type *type = mdev->type;
	struct pci_sim_mdev_parent *mp;
	int type_idx;

	if (!state)
		return;

	mp = container_of(type->parent, struct pci_sim_mdev_parent, parent);
	type_idx = state->type_idx;

	vfio_unregister_group_dev(&state->vdev);
	vfio_put_device(&state->vdev);
	atomic_inc(&mp->avail[type_idx]);
	dev_info(&mdev->dev, "mdev instance removed (type %d)\n", type_idx);
}

static unsigned int pci_sim_mdev_get_available(struct mdev_type *type)
{
	struct pci_sim_mdev_parent *mp;
	int type_idx;

	mp = container_of(type->parent, struct pci_sim_mdev_parent, parent);

	for (type_idx = 0; type_idx < PCI_SIM_MDEV_NUM_TYPES; type_idx++) {
		if (&mp->types[type_idx] == type)
			return atomic_read(&mp->avail[type_idx]);
	}
	return 0;
}

static ssize_t pci_sim_mdev_show_description(struct mdev_type *type, char *buf)
{
	struct pci_sim_mdev_parent *mp;
	int type_idx;

	mp = container_of(type->parent, struct pci_sim_mdev_parent, parent);

	for (type_idx = 0; type_idx < PCI_SIM_MDEV_NUM_TYPES; type_idx++) {
		if (&mp->types[type_idx] == type)
			return sysfs_emit(buf, "%s\n",
					  pci_sim_mdev_descriptions[type_idx]);
	}
	return sysfs_emit(buf, "unknown type\n");
}

static struct mdev_driver pci_sim_mdev_driver = {
	.device_api = VFIO_DEVICE_API_PCI_STRING,
	.max_instances = 0,
	.driver = {
		.name = "pci_sim_mdev",
		.owner = THIS_MODULE,
		.mod_name = KBUILD_MODNAME,
	},
	.probe = pci_sim_mdev_probe,
	.remove = pci_sim_mdev_remove,
	.get_available = pci_sim_mdev_get_available,
	.show_description = pci_sim_mdev_show_description,
};

/* ---- Registration helpers ---------------------------------------------- */

int pci_sim_mdev_register_driver(void)
{
	return mdev_register_driver(&pci_sim_mdev_driver);
}

void pci_sim_mdev_unregister_driver(void)
{
	mdev_unregister_driver(&pci_sim_mdev_driver);
}

int pci_sim_mdev_register_parent(struct fake_pci_host *host)
{
	struct pci_sim_mdev_parent *mp;
	struct pci_dev *pf_pdev;
	unsigned int small_inst, large_inst;
	int ret;

	if (!host->bridge || !host->bridge->bus)
		return -ENODEV;

	pf_pdev = pci_get_slot(host->bridge->bus, PCI_DEVFN(0, 0));
	if (!pf_pdev) {
		pr_err("fake_pci: mdev: PF not found on domain %04x\n",
		       host->domain_nr);
		return -ENODEV;
	}

	mp = kzalloc(sizeof(*mp), GFP_KERNEL);
	if (!mp) {
		pci_dev_put(pf_pdev);
		return -ENOMEM;
	}

	small_inst = mdev_instances;
	large_inst = max(mdev_instances / 4, 1U);

	atomic_set(&mp->avail[PCI_SIM_MDEV_SMALL_IDX], small_inst);
	atomic_set(&mp->avail[PCI_SIM_MDEV_LARGE_IDX], large_inst);

	mp->types[PCI_SIM_MDEV_SMALL_IDX].sysfs_name = "sim_accel_small";
	mp->types[PCI_SIM_MDEV_SMALL_IDX].pretty_name =
		pci_sim_mdev_names[PCI_SIM_MDEV_SMALL_IDX];

	mp->types[PCI_SIM_MDEV_LARGE_IDX].sysfs_name = "sim_accel_large";
	mp->types[PCI_SIM_MDEV_LARGE_IDX].pretty_name =
		pci_sim_mdev_names[PCI_SIM_MDEV_LARGE_IDX];

	mp->type_ptrs[PCI_SIM_MDEV_SMALL_IDX] =
		&mp->types[PCI_SIM_MDEV_SMALL_IDX];
	mp->type_ptrs[PCI_SIM_MDEV_LARGE_IDX] =
		&mp->types[PCI_SIM_MDEV_LARGE_IDX];

	ret = mdev_register_parent(&mp->parent, &pf_pdev->dev,
				   &pci_sim_mdev_driver, mp->type_ptrs,
				   PCI_SIM_MDEV_NUM_TYPES);
	if (ret) {
		pr_err("fake_pci: mdev_register_parent failed on domain %04x: %d\n",
		       host->domain_nr, ret);
		kfree(mp);
		pci_dev_put(pf_pdev);
		return ret;
	}

	host->mdev_parent = mp;
	pci_dev_put(pf_pdev);

	pr_info("fake_pci: mdev parent registered on domain %04x (%u small, %u large)\n",
		host->domain_nr, small_inst, large_inst);
	return 0;
}

void pci_sim_mdev_unregister_parent(struct fake_pci_host *host)
{
	if (!host->mdev_parent)
		return;

	mdev_unregister_parent(&host->mdev_parent->parent);
	kfree(host->mdev_parent);
	host->mdev_parent = NULL;
}

#endif /* PCI_SIM_HAS_MDEV */
