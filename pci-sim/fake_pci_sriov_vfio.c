// SPDX-License-Identifier: GPL-2.0
/*
 * Fake PCI SR-IOV VFIO test fixture -- VFIO PCI device driver
 *
 * Generic vfio-pci expects BAR0 to be backed by real host MMIO.  The fake VFs
 * only exist behind fake pci_ops, so pci_iomap()/ioread() cannot service guest
 * BAR accesses.  This override-only driver still exposes the VF via VFIO, but
 * traps BAR0 accesses and emulates a tiny 16550 loopback UART.  When
 * vfio_guest_8250_compat is set, the guest config-space vendor/device IDs are
 * overlaid with the SGI IOC3 serial identity so the guest 8250_pci driver
 * binds automatically.
 */

#include "fake_pci_sriov.h"

static int pci_sim_vfio_open_device(struct vfio_device *core_vdev)
{
	struct pci_sim_vfio_vf *sim = container_of(core_vdev,
			struct pci_sim_vfio_vf, core.vdev);
	int ret;

	ret = vfio_pci_core_enable(&sim->core);
	if (ret)
		return ret;

	pci_sim_uart_reset(&sim->uart);
	vfio_pci_core_finish_enable(&sim->core);
	return 0;
}

static bool pci_sim_vfio_bar0_uart_reg(loff_t pos, u8 *reg)
{
	loff_t offset;

	if (vfio_guest_8250_compat) {
		if (pos < PCI_SIM_SGI_IOC3_UART_OFFSET ||
		    pos >= PCI_SIM_SGI_IOC3_UART_OFFSET + 8)
			return false;
		offset = pos - PCI_SIM_SGI_IOC3_UART_OFFSET;
	} else {
		if (pos >= 8)
			return false;
		offset = pos;
	}

	*reg = offset;
	return true;
}

static ssize_t pci_sim_vfio_bar0_rw(struct pci_sim_vfio_vf *sim,
				    char __user *buf, size_t count,
				    loff_t *ppos, bool iswrite)
{
	loff_t pos = *ppos & VFIO_PCI_OFFSET_MASK;
	size_t done;
	u8 reg, val;

	if (pos >= PCI_SIM_VFIO_BAR0_SIZE)
		return -EINVAL;

	count = min_t(size_t, count, PCI_SIM_VFIO_BAR0_SIZE - pos);

	mutex_lock(&sim->lock);
	for (done = 0; done < count; done++) {
		if (iswrite) {
			if (copy_from_user(&val, buf + done, 1)) {
				mutex_unlock(&sim->lock);
				return done ?: -EFAULT;
			}
			if (!pci_sim_vfio_bar0_uart_reg(pos + done, &reg))
				continue;

			if (vfio_uart_trace)
				pr_info("fake_pci: vfio uart W off=0x%llx reg=%u val=0x%02x\n",
					(unsigned long long)(pos + done), reg, val);
			pci_sim_uart_write_reg(&sim->uart, reg, val);
		} else {
			if (pci_sim_vfio_bar0_uart_reg(pos + done, &reg)) {
				val = pci_sim_uart_read_reg(&sim->uart, reg);
				if (vfio_uart_trace)
					pr_info("fake_pci: vfio uart R off=0x%llx reg=%u val=0x%02x\n",
						(unsigned long long)(pos + done), reg, val);
			} else {
				val = 0xff;
			}
			if (copy_to_user(buf + done, &val, 1)) {
				mutex_unlock(&sim->lock);
				return done ?: -EFAULT;
			}
		}
	}
	mutex_unlock(&sim->lock);

	*ppos += done;
	return done;
}

static int pci_sim_vfio_copy_config_value(char __user *buf,
					  loff_t pos, size_t count,
					  unsigned int reg, const void *val,
					  size_t val_size)
{
	loff_t copy_offset;
	size_t copy_count, register_offset;

	if (!vfio_pci_core_range_intersect_range(pos, count, reg, val_size,
					       &copy_offset, &copy_count,
					       &register_offset))
		return 0;

	if (copy_to_user(buf + copy_offset, val + register_offset, copy_count))
		return -EFAULT;

	return 0;
}

static ssize_t pci_sim_vfio_read_config(struct vfio_device *core_vdev,
					char __user *buf, size_t count,
					loff_t *ppos)
{
	loff_t pos = *ppos & VFIO_PCI_OFFSET_MASK;
	__le16 val16;
	__le32 val32;
	ssize_t ret;
	size_t done;

	ret = vfio_pci_core_read(core_vdev, buf, count, ppos);
	if (ret <= 0 || !vfio_guest_8250_compat)
		return ret;
	done = ret;

	val16 = cpu_to_le16(PCI_VENDOR_ID_SGI);
	if (pci_sim_vfio_copy_config_value(buf, pos, done, PCI_VENDOR_ID,
					   &val16, sizeof(val16)))
		return -EFAULT;

	val16 = cpu_to_le16(PCI_DEVICE_ID_SGI_IOC3);
	if (pci_sim_vfio_copy_config_value(buf, pos, done, PCI_DEVICE_ID,
					   &val16, sizeof(val16)))
		return -EFAULT;

	val32 = cpu_to_le32(FAKE_PCI_SERIAL_CLASS << 8);
	if (pci_sim_vfio_copy_config_value(buf, pos, done, PCI_CLASS_REVISION,
					   &val32, sizeof(val32)))
		return -EFAULT;

	val16 = cpu_to_le16(0xff00);
	if (pci_sim_vfio_copy_config_value(buf, pos, done,
					   PCI_SUBSYSTEM_VENDOR_ID,
					   &val16, sizeof(val16)))
		return -EFAULT;

	val16 = cpu_to_le16(0);
	if (pci_sim_vfio_copy_config_value(buf, pos, done, PCI_SUBSYSTEM_ID,
					   &val16, sizeof(val16)))
		return -EFAULT;

	return ret;
}

static ssize_t pci_sim_vfio_read(struct vfio_device *core_vdev,
				 char __user *buf, size_t count, loff_t *ppos)
{
	struct pci_sim_vfio_vf *sim = container_of(core_vdev,
			struct pci_sim_vfio_vf, core.vdev);
	unsigned int index = VFIO_PCI_OFFSET_TO_INDEX(*ppos);

	if (!count)
		return 0;

	if (index == VFIO_PCI_CONFIG_REGION_INDEX)
		return pci_sim_vfio_read_config(core_vdev, buf, count, ppos);

	if (index == VFIO_PCI_BAR0_REGION_INDEX)
		return pci_sim_vfio_bar0_rw(sim, buf, count, ppos, false);

	return vfio_pci_core_read(core_vdev, buf, count, ppos);
}

static ssize_t pci_sim_vfio_write(struct vfio_device *core_vdev,
				  const char __user *buf, size_t count,
				  loff_t *ppos)
{
	struct pci_sim_vfio_vf *sim = container_of(core_vdev,
			struct pci_sim_vfio_vf, core.vdev);
	unsigned int index = VFIO_PCI_OFFSET_TO_INDEX(*ppos);

	if (!count)
		return 0;

	if (index == VFIO_PCI_BAR0_REGION_INDEX)
		return pci_sim_vfio_bar0_rw(sim, (char __user *)buf, count,
					    ppos, true);

	return vfio_pci_core_write(core_vdev, buf, count, ppos);
}

#if PCI_SIM_VFIO_HAS_GET_REGION_INFO_CAPS
static int pci_sim_vfio_get_region_info(struct vfio_device *core_vdev,
					struct vfio_region_info *info,
					struct vfio_info_cap *caps)
{
	if (info->index != VFIO_PCI_BAR0_REGION_INDEX)
		return vfio_pci_ioctl_get_region_info(core_vdev, info, caps);

	info->offset = VFIO_PCI_INDEX_TO_OFFSET(info->index);
	info->size = vfio_guest_8250_compat ? PCI_SIM_VFIO_BAR0_SIZE : BAR0_SIZE;
	info->flags = VFIO_REGION_INFO_FLAG_READ | VFIO_REGION_INFO_FLAG_WRITE;
	return 0;
}
#else
static long pci_sim_vfio_ioctl(struct vfio_device *core_vdev, unsigned int cmd,
			       unsigned long arg)
{
	struct vfio_region_info info;
	void __user *uarg = (void __user *)arg;

	if (cmd != VFIO_DEVICE_GET_REGION_INFO)
		return vfio_pci_core_ioctl(core_vdev, cmd, arg);

	if (copy_from_user(&info, uarg, sizeof(info)))
		return -EFAULT;

	if (info.index != VFIO_PCI_BAR0_REGION_INDEX)
		return vfio_pci_core_ioctl(core_vdev, cmd, arg);

	if (info.argsz < sizeof(info))
		return -EINVAL;

	info.offset = VFIO_PCI_INDEX_TO_OFFSET(info.index);
	info.size = vfio_guest_8250_compat ? PCI_SIM_VFIO_BAR0_SIZE : BAR0_SIZE;
	info.flags = VFIO_REGION_INFO_FLAG_READ | VFIO_REGION_INFO_FLAG_WRITE;
	info.cap_offset = 0;

	if (copy_to_user(uarg, &info, sizeof(info)))
		return -EFAULT;

	return 0;
}
#endif

static int pci_sim_vfio_mmap(struct vfio_device *core_vdev,
			     struct vm_area_struct *vma)
{
	unsigned int index = vma->vm_pgoff >> (VFIO_PCI_OFFSET_SHIFT - PAGE_SHIFT);

	if (index == VFIO_PCI_BAR0_REGION_INDEX)
		return -EINVAL;

	return vfio_pci_core_mmap(core_vdev, vma);
}

static const struct vfio_device_ops pci_sim_vfio_ops = {
	.name		= "pci_sim_vfio_pci",
	.init		= vfio_pci_core_init_dev,
	.release	= vfio_pci_core_release_dev,
	.open_device	= pci_sim_vfio_open_device,
	.close_device	= vfio_pci_core_close_device,
#if PCI_SIM_VFIO_HAS_GET_REGION_INFO_CAPS
	.ioctl		= vfio_pci_core_ioctl,
	.get_region_info_caps = pci_sim_vfio_get_region_info,
#else
	.ioctl		= pci_sim_vfio_ioctl,
#endif
	.device_feature	= vfio_pci_core_ioctl_feature,
	.read		= pci_sim_vfio_read,
	.write		= pci_sim_vfio_write,
	.mmap		= pci_sim_vfio_mmap,
	.request	= vfio_pci_core_request,
	.match		= vfio_pci_core_match,
#if PCI_SIM_VFIO_HAS_MATCH_TOKEN_UUID
	.match_token_uuid = vfio_pci_core_match_token_uuid,
#endif
	.bind_iommufd	= vfio_iommufd_physical_bind,
	.unbind_iommufd	= vfio_iommufd_physical_unbind,
	.attach_ioas	= vfio_iommufd_physical_attach_ioas,
	.detach_ioas	= vfio_iommufd_physical_detach_ioas,
#if PCI_SIM_VFIO_HAS_PASID_IOAS
	.pasid_attach_ioas = vfio_iommufd_physical_pasid_attach_ioas,
	.pasid_detach_ioas = vfio_iommufd_physical_pasid_detach_ioas,
#endif
};

static int pci_sim_vfio_probe(struct pci_dev *pdev,
			      const struct pci_device_id *id)
{
	struct pci_sim_vfio_vf *sim;
	int ret;

	sim = vfio_alloc_device(pci_sim_vfio_vf, core.vdev, &pdev->dev,
				&pci_sim_vfio_ops);
	if (IS_ERR(sim))
		return PTR_ERR(sim);

	mutex_init(&sim->lock);
	pci_sim_uart_init(&sim->uart);
	dev_set_drvdata(&pdev->dev, &sim->core);

	ret = vfio_pci_core_register_device(&sim->core);
	if (ret)
		goto err_put;

	pci_info(pdev, "registered VFIO UART BAR0 emulator\n");
	return 0;

err_put:
	vfio_put_device(&sim->core.vdev);
	return ret;
}

static void pci_sim_vfio_remove(struct pci_dev *pdev)
{
	struct vfio_pci_core_device *core = dev_get_drvdata(&pdev->dev);
	struct pci_sim_vfio_vf *sim;

	if (!core)
		return;

	sim = container_of(core, struct pci_sim_vfio_vf, core);
	vfio_pci_core_unregister_device(&sim->core);
	vfio_put_device(&sim->core.vdev);
}

static const struct pci_device_id pci_sim_vfio_ids[] = {
	{ PCI_DRIVER_OVERRIDE_DEVICE_VFIO(FAKE_PCI_VENDOR_ID,
					  FAKE_PCI_VF_DEVICE_ID) },
	{ }
};
MODULE_DEVICE_TABLE(pci, pci_sim_vfio_ids);

struct pci_driver pci_sim_vfio_driver = {
	.name			= "pci_sim_vfio_pci",
	.id_table		= pci_sim_vfio_ids,
	.probe			= pci_sim_vfio_probe,
	.remove			= pci_sim_vfio_remove,
	.err_handler		= &vfio_pci_core_err_handlers,
	.driver_managed_dma	= true,
};
