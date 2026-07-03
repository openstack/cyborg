/* SPDX-License-Identifier: GPL-2.0 */
/*
 * Fake PCI SR-IOV VFIO test fixture -- shared internal header
 *
 * All compilation units in the fake_pci_sriov multi-file module include this
 * header.  It centralises struct definitions, constants, and cross-file
 * declarations so individual source files stay focused on a single subsystem.
 */

#ifndef FAKE_PCI_SRIOV_H
#define FAKE_PCI_SRIOV_H

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/pci.h>
#include <linux/pci_regs.h>
#include <linux/platform_device.h>
#include <linux/iommu.h>
#include <linux/slab.h>
#include <linux/mutex.h>
#include <linux/xarray.h>
#include <linux/serial_reg.h>
#include <linux/tty.h>
#include <linux/tty_flip.h>
#include <linux/uaccess.h>
#include <linux/vfio_pci_core.h>
#include <linux/string.h>
#include <linux/unaligned.h>
#include <linux/ioport.h>
#include <linux/list.h>

#include "fake_pci_sriov_compat.h"

#ifdef CONFIG_X86
#include <asm/pci.h>
#elif defined(CONFIG_ACPI)
#include <linux/pci-ecam.h>
#endif

/* Device identification */

#define FAKE_PCI_VENDOR_ID 0x1d55
#define FAKE_PCI_PF_DEVICE_ID 0x1000
#define FAKE_PCI_VF_DEVICE_ID 0x1001
#define FAKE_PCI_SERIAL_CLASS 0x070002 /* Serial controller, 16550 */
#define FAKE_PCI_VENDOR_CLASS 0xff0000
#define FAKE_PCI_SUBSYS_VENDOR FAKE_PCI_VENDOR_ID
#define FAKE_PCI_SUBSYS_ID FAKE_PCI_PF_DEVICE_ID

/* SR-IOV / BAR configuration */

#define MAX_VFS 7
#define FAKE_PCI_MAX_HOSTS 16
#define SRIOV_CAP_OFFSET 0x100
#define PCIE_CAP_OFFSET 0x40

#define BAR0_SIZE 0x1000
#define FAKE_PCI_MEM_BASE 0xd0000000ULL
#define FAKE_PCI_MEM_64_BASE 0x100000000ULL
#define FAKE_PCI_MEM_STRIDE 0x00100000
#define FAKE_PCI_MEM_MIN_SIZE (BAR0_SIZE * (MAX_VFS + 1))
#define FAKE_PCI_BAR_FLAGS PCI_BASE_ADDRESS_MEM_TYPE_64
#define PCI_SIM_VFIO_BAR0_SIZE 0x40000
#define PCI_SIM_SGI_IOC3_UART_OFFSET 0x20178

/* Host-side TTY loopback */

#define PCI_SIM_TTY_NAME "ttyPCI_SIM"
#define PCI_SIM_MAX_TTYS 256
#define PCI_SIM_UART_FIFO_SIZE 4096
#define PCI_SIM_UART_CHUNK 256

/* Data structures */

struct fake_pci_device {
	u8 config_space[4096];
	bool present;
	bool is_vf;
	int vf_index;
};

struct fake_pci_host {
	struct list_head list;
	struct pci_host_bridge *bridge;
	struct platform_device *pdev;
#ifdef CONFIG_X86
	struct pci_sysdata sysdata;
#elif defined(CONFIG_ACPI)
	struct pci_config_window sysdata;
#endif
	struct resource bus_resource;
	struct resource mem_resource;
	bool mem_resource_registered;
	struct fake_pci_device pf;
	struct fake_pci_device vfs[MAX_VFS];
	int num_vfs_enabled;
	int domain_nr;
	struct mutex lock; /* Protects VF enable/disable state. */
};

struct pci_sim_uart {
	spinlock_t lock; /* Protects UART registers and FIFO state. */
	u8 regs[8];
	u8 fifo[PCI_SIM_UART_FIFO_SIZE];
	unsigned int head;
	unsigned int tail;
	unsigned int count;
	bool dlab;
	bool overrun;
	u16 divisor;
	u8 fcr;
	u8 intr_trigger_level;
};

struct pci_sim_vf_tty {
	struct pci_dev *pdev;
	struct tty_port port;
	struct mutex state_lock; /* Protects dead flag and tty writes. */
	struct pci_sim_uart uart;
	int id;
	bool dead;
};

struct pci_sim_vfio_vf {
	struct vfio_pci_core_device core;
	struct mutex lock; /* Serializes VFIO BAR0 access. */
	struct pci_sim_uart uart;
};

/* Cross-file globals (defined in the owning .c, declared extern here) */

/* fake_pci_sriov_core.c */
extern struct list_head fake_hosts;
extern struct mutex fake_hosts_lock;

/* Module parameters that multiple files read */
extern bool vf_serial_class;
extern bool vfio_guest_8250_compat;
extern bool vfio_uart_trace;
extern unsigned long mem_stride;

/* fake_pci_sriov_iommu.c */
extern struct iommu_device fake_iommu_dev;
extern struct platform_device *fake_iommu_pdev;

/* Cross-file function declarations */

/* fake_pci_sriov_cfg.c */
void init_pf_config_space(struct fake_pci_device *dev);
struct fake_pci_host *fake_pci_host_from_domain(int domain);

/* fake_pci_sriov_uart.c */
int pci_sim_tty_register_driver(void);
void pci_sim_tty_unregister_driver(void);

/* UART primitives also used by vfio.c */
void pci_sim_uart_reset(struct pci_sim_uart *uart);
void pci_sim_uart_init(struct pci_sim_uart *uart);
size_t pci_sim_uart_write_data(struct pci_sim_uart *uart, const u8 *buf,
			       size_t len);
unsigned int pci_sim_uart_write_room(struct pci_sim_uart *uart);
unsigned int pci_sim_uart_chars_in_buffer(struct pci_sim_uart *uart);
u8 pci_sim_uart_lsr(struct pci_sim_uart *uart);
u8 pci_sim_uart_read_data(struct pci_sim_uart *uart);
u8 pci_sim_uart_read_reg(struct pci_sim_uart *uart, u8 reg);
void pci_sim_uart_write_reg(struct pci_sim_uart *uart, u8 reg, u8 val);

/* fake_pci_sriov_iommu.c (ops table used by core init) */
extern const struct iommu_ops fake_iommu_ops;

/* fake_pci_sriov_cfg.c (pci_ops used by core host-probe) */
extern struct pci_ops fake_pci_ops;

/* PCI drivers registered by core init */
extern struct pci_driver fake_pci_pf_driver;
extern struct pci_driver pci_sim_vf_driver;
extern struct pci_driver pci_sim_vfio_driver;

#endif /* FAKE_PCI_SRIOV_H */
