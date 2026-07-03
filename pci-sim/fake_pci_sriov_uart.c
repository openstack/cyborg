// SPDX-License-Identifier: GPL-2.0
/*
 * Fake PCI SR-IOV VFIO test fixture -- host-side VF TTY loopback driver
 *
 * Each fake VF is claimed by pci_sim_loopback_vf.  The driver presents the VF
 * as a /dev/ttyPCI_SIM<N> character device backed by an in-kernel 16550-style
 * UART FIFO.  Bytes written to the tty are echoed back so that a host-side
 * process (or the VFIO guest via the companion vfio.c driver) can verify the
 * loopback path end-to-end.
 */

#include "fake_pci_sriov.h"

static DEFINE_XARRAY_ALLOC(pci_sim_tty_xa);
static DEFINE_MUTEX(pci_sim_tty_xa_lock); /* Serializes TTY ID lookup/removal. */
static struct tty_driver *pci_sim_tty_driver;

/* 16550-compatible UART emulation */

void pci_sim_uart_reset(struct pci_sim_uart *uart)
{
	unsigned long flags;

	spin_lock_irqsave(&uart->lock, flags);
	memset(uart->regs, 0, sizeof(uart->regs));
	uart->head = 0;
	uart->tail = 0;
	uart->count = 0;
	uart->dlab = false;
	uart->overrun = false;
	uart->divisor = 0;
	uart->fcr = 0;
	uart->intr_trigger_level = 1;
	uart->regs[UART_LSR] = UART_LSR_TEMT | UART_LSR_THRE;
	uart->regs[UART_MSR] = UART_MSR_DSR | UART_MSR_DCD | UART_MSR_CTS;
	spin_unlock_irqrestore(&uart->lock, flags);
}

void pci_sim_uart_init(struct pci_sim_uart *uart)
{
	spin_lock_init(&uart->lock);
	pci_sim_uart_reset(uart);
}

static unsigned int pci_sim_uart_space_locked(struct pci_sim_uart *uart)
{
	return PCI_SIM_UART_FIFO_SIZE - uart->count;
}

size_t pci_sim_uart_write_data(struct pci_sim_uart *uart, const u8 *buf,
			       size_t len)
{
	unsigned long flags;
	size_t copied, i;

	spin_lock_irqsave(&uart->lock, flags);
	copied = min_t(size_t, len, pci_sim_uart_space_locked(uart));

	for (i = 0; i < copied; i++) {
		uart->fifo[uart->head] = buf[i];
		uart->head = (uart->head + 1) % PCI_SIM_UART_FIFO_SIZE;
		uart->count++;
	}

	uart->overrun = (copied < len);
	spin_unlock_irqrestore(&uart->lock, flags);

	return copied;
}

static size_t pci_sim_uart_peek_data(struct pci_sim_uart *uart, u8 *buf,
				     size_t len)
{
	unsigned long flags;
	size_t copied, i;
	unsigned int tail;

	spin_lock_irqsave(&uart->lock, flags);
	copied = min_t(size_t, len, uart->count);
	tail = uart->tail;

	for (i = 0; i < copied; i++) {
		buf[i] = uart->fifo[tail];
		tail = (tail + 1) % PCI_SIM_UART_FIFO_SIZE;
	}

	spin_unlock_irqrestore(&uart->lock, flags);

	return copied;
}

static void pci_sim_uart_consume_data(struct pci_sim_uart *uart, size_t len)
{
	unsigned long flags;

	spin_lock_irqsave(&uart->lock, flags);
	len = min_t(size_t, len, uart->count);
	uart->tail = (uart->tail + len) % PCI_SIM_UART_FIFO_SIZE;
	uart->count -= len;
	spin_unlock_irqrestore(&uart->lock, flags);
}

unsigned int pci_sim_uart_write_room(struct pci_sim_uart *uart)
{
	unsigned long flags;
	unsigned int room;

	spin_lock_irqsave(&uart->lock, flags);
	room = pci_sim_uart_space_locked(uart);
	spin_unlock_irqrestore(&uart->lock, flags);

	return room;
}

unsigned int pci_sim_uart_chars_in_buffer(struct pci_sim_uart *uart)
{
	unsigned long flags;
	unsigned int count;

	spin_lock_irqsave(&uart->lock, flags);
	count = uart->count;
	spin_unlock_irqrestore(&uart->lock, flags);

	return count;
}

u8 pci_sim_uart_lsr(struct pci_sim_uart *uart)
{
	unsigned long flags;
	u8 lsr = UART_LSR_TEMT | UART_LSR_THRE;

	spin_lock_irqsave(&uart->lock, flags);
	if (uart->count)
		lsr |= UART_LSR_DR;
	if (uart->overrun)
		lsr |= UART_LSR_OE;
	spin_unlock_irqrestore(&uart->lock, flags);

	return lsr;
}

u8 pci_sim_uart_read_data(struct pci_sim_uart *uart)
{
	unsigned long flags;
	u8 val = 0xff;

	spin_lock_irqsave(&uart->lock, flags);
	if (uart->count) {
		val = uart->fifo[uart->tail];
		uart->tail = (uart->tail + 1) % PCI_SIM_UART_FIFO_SIZE;
		uart->count--;
	}
	spin_unlock_irqrestore(&uart->lock, flags);

	return val;
}

static u8 pci_sim_uart_iir(struct pci_sim_uart *uart)
{
	unsigned long flags;
	u8 iir, ier;

	spin_lock_irqsave(&uart->lock, flags);
	ier = uart->regs[UART_IER];

	if ((ier & UART_IER_RLSI) && uart->overrun)
		iir = UART_IIR_RLSI;
	else if ((ier & UART_IER_RDI) &&
		 uart->count >= uart->intr_trigger_level)
		iir = UART_IIR_RDI;
	else if (ier & UART_IER_THRI)
		iir = UART_IIR_THRI;
	else if ((ier & UART_IER_MSI) &&
		 (uart->regs[UART_MCR] & (UART_MCR_RTS | UART_MCR_DTR)))
		iir = UART_IIR_MSI;
	else
		iir = UART_IIR_NO_INT;

	if (uart->fcr & UART_FCR_ENABLE_FIFO)
		iir |= UART_IIR_FIFO_ENABLED_16550A;

	spin_unlock_irqrestore(&uart->lock, flags);

	return iir;
}

static void pci_sim_uart_clear_fifo(struct pci_sim_uart *uart)
{
	unsigned long flags;

	spin_lock_irqsave(&uart->lock, flags);
	uart->head = 0;
	uart->tail = 0;
	uart->count = 0;
	uart->overrun = false;
	spin_unlock_irqrestore(&uart->lock, flags);
}

u8 pci_sim_uart_read_reg(struct pci_sim_uart *uart, u8 reg)
{
	reg &= 7;

	if (uart->dlab) {
		switch (reg) {
		case UART_DLL:
			return uart->divisor & 0xff;
		case UART_DLM:
			return uart->divisor >> 8;
		}
	}

	switch (reg) {
	case UART_RX:
		return pci_sim_uart_read_data(uart);
	case UART_IER:
		return uart->regs[UART_IER] & 0x0f;
	case UART_IIR:
		return pci_sim_uart_iir(uart);
	case UART_LCR:
		return uart->regs[UART_LCR];
	case UART_MCR:
		return uart->regs[UART_MCR];
	case UART_LSR:
		return pci_sim_uart_lsr(uart);
	case UART_MSR:
		return uart->regs[UART_MSR];
	case UART_SCR:
		return uart->regs[UART_SCR];
	default:
		return 0xff;
	}
}

void pci_sim_uart_write_reg(struct pci_sim_uart *uart, u8 reg, u8 val)
{
	reg &= 7;

	if (uart->dlab) {
		switch (reg) {
		case UART_DLL:
			uart->divisor = (uart->divisor & 0xff00) | val;
			return;
		case UART_DLM:
			uart->divisor = (uart->divisor & 0x00ff) | (val << 8);
			return;
		}
	}

	switch (reg) {
	case UART_TX:
		pci_sim_uart_write_data(uart, &val, 1);
		break;
	case UART_IER:
		uart->regs[UART_IER] = val & 0x0f;
		break;
	case UART_FCR:
		uart->fcr = val;
		switch (val & UART_FCR_TRIGGER_MASK) {
		case UART_FCR_TRIGGER_1:
			uart->intr_trigger_level = 1;
			break;
		case UART_FCR_TRIGGER_4:
			uart->intr_trigger_level = 4;
			break;
		case UART_FCR_TRIGGER_8:
			uart->intr_trigger_level = 8;
			break;
		case UART_FCR_TRIGGER_14:
			uart->intr_trigger_level = 14;
			break;
		}
		if (val & (UART_FCR_CLEAR_RCVR | UART_FCR_CLEAR_XMIT))
			pci_sim_uart_clear_fifo(uart);
		break;
	case UART_LCR:
		uart->regs[UART_LCR] = val;
		uart->dlab = !!(val & UART_LCR_DLAB);
		break;
	case UART_MCR:
		uart->regs[UART_MCR] = val;
		break;
	case UART_SCR:
		uart->regs[UART_SCR] = val;
		break;
	default:
		break;
	}
}

/* VF TTY loopback helper */

static void pci_sim_vf_flush_to_tty(struct pci_sim_vf_tty *vf)
{
	u8 buf[PCI_SIM_UART_CHUNK];
	size_t copied, pending;
	unsigned int room;
	bool pushed = false;

	for (;;) {
		room = tty_buffer_space_avail(&vf->port);
		if (!room)
			break;

		pending = pci_sim_uart_peek_data(&vf->uart, buf,
						 min_t(size_t, sizeof(buf),
						       room));
		if (!pending)
			break;

		copied = tty_insert_flip_string(&vf->port, buf, pending);
		if (!copied)
			break;

		pci_sim_uart_consume_data(&vf->uart, copied);
		pushed = true;

		if (copied < pending)
			break;
	}

	if (pushed)
		tty_flip_buffer_push(&vf->port);
}

/* TTY driver operations */

static int pci_sim_tty_install(struct tty_driver *driver,
			       struct tty_struct *tty)
{
	struct pci_sim_vf_tty *vf;
	struct tty_port *port;
	int ret;

	mutex_lock(&pci_sim_tty_xa_lock);
	vf = xa_load(&pci_sim_tty_xa, tty->index);
	if (vf)
		port = tty_port_get(&vf->port);
	else
		port = NULL;
	mutex_unlock(&pci_sim_tty_xa_lock);

	if (!port)
		return -ENODEV;

	tty->driver_data = vf;
	ret = tty_port_install(port, driver, tty);
	if (ret)
		tty_port_put(port);

	return ret;
}

static void pci_sim_tty_cleanup(struct tty_struct *tty)
{
	tty_port_put(tty->port);
}

static int pci_sim_tty_open(struct tty_struct *tty, struct file *filp)
{
	struct pci_sim_vf_tty *vf = tty->driver_data;
	int ret;

	mutex_lock(&vf->state_lock);
	ret = vf->dead ? -ENODEV : 0;
	mutex_unlock(&vf->state_lock);
	if (ret)
		return ret;

	return tty_port_open(tty->port, tty, filp);
}

static void pci_sim_tty_close(struct tty_struct *tty, struct file *filp)
{
	tty_port_close(tty->port, tty, filp);
}

static ssize_t pci_sim_tty_write(struct tty_struct *tty, const u8 *buf,
				 size_t len)
{
	struct pci_sim_vf_tty *vf = tty->driver_data;
	size_t copied;

	if (!len)
		return 0;

	mutex_lock(&vf->state_lock);
	if (vf->dead) {
		mutex_unlock(&vf->state_lock);
		return -ENODEV;
	}

	copied = pci_sim_uart_write_data(&vf->uart, buf, len);
	pci_sim_vf_flush_to_tty(vf);
	mutex_unlock(&vf->state_lock);

	return copied;
}

static unsigned int pci_sim_tty_write_room(struct tty_struct *tty)
{
	struct pci_sim_vf_tty *vf = tty->driver_data;

	if (!vf)
		return 0;

	return pci_sim_uart_write_room(&vf->uart);
}

static unsigned int pci_sim_tty_chars_in_buffer(struct tty_struct *tty)
{
	struct pci_sim_vf_tty *vf = tty->driver_data;

	if (!vf)
		return 0;

	return pci_sim_uart_chars_in_buffer(&vf->uart);
}

static void pci_sim_tty_hangup(struct tty_struct *tty)
{
	tty_port_hangup(tty->port);
}

static const struct tty_operations pci_sim_tty_ops = {
	.install = pci_sim_tty_install,
	.open = pci_sim_tty_open,
	.close = pci_sim_tty_close,
	.write = pci_sim_tty_write,
	.write_room = pci_sim_tty_write_room,
	.chars_in_buffer = pci_sim_tty_chars_in_buffer,
	.hangup = pci_sim_tty_hangup,
	.cleanup = pci_sim_tty_cleanup,
};

static void pci_sim_tty_destruct_port(struct tty_port *port)
{
	struct pci_sim_vf_tty *vf =
		container_of(port, struct pci_sim_vf_tty, port);

	mutex_lock(&pci_sim_tty_xa_lock);
	if (vf->id >= 0)
		xa_erase(&pci_sim_tty_xa, vf->id);
	mutex_unlock(&pci_sim_tty_xa_lock);

	kfree(vf);
}

static const struct tty_port_operations pci_sim_tty_port_ops = {
	.destruct = pci_sim_tty_destruct_port,
};

/* VF PCI driver */

static int pci_sim_vf_probe(struct pci_dev *pdev,
			    const struct pci_device_id *id)
{
	struct pci_sim_vf_tty *vf;
	struct device *tty_dev;
	u32 tty_id;
	int ret;

	ret = pci_enable_device(pdev);
	if (ret)
		return ret;

	vf = kzalloc(sizeof(*vf), GFP_KERNEL);
	if (!vf) {
		ret = -ENOMEM;
		goto err_disable;
	}

	vf->pdev = pdev;
	vf->id = -1;
	mutex_init(&vf->state_lock);
	pci_sim_uart_init(&vf->uart);

	mutex_lock(&pci_sim_tty_xa_lock);
	ret = xa_alloc(&pci_sim_tty_xa, &tty_id, vf,
		       XA_LIMIT(0, PCI_SIM_MAX_TTYS - 1), GFP_KERNEL);
	mutex_unlock(&pci_sim_tty_xa_lock);
	if (ret)
		goto err_free;
	vf->id = tty_id;

	tty_port_init(&vf->port);
	vf->port.ops = &pci_sim_tty_port_ops;

	tty_dev = tty_port_register_device(&vf->port, pci_sim_tty_driver,
					   vf->id, &pdev->dev);
	if (IS_ERR(tty_dev)) {
		ret = PTR_ERR(tty_dev);
		goto err_put_port;
	}

	pci_set_drvdata(pdev, vf);
	pci_info(pdev, "registered /dev/%s%d, lsr=0x%02x\n", PCI_SIM_TTY_NAME,
		 vf->id, pci_sim_uart_lsr(&vf->uart));

	return 0;

err_put_port:
	tty_port_put(&vf->port);
	pci_disable_device(pdev);
	return ret;
err_free:
	kfree(vf);
err_disable:
	pci_disable_device(pdev);
	return ret;
}

static void pci_sim_vf_remove(struct pci_dev *pdev)
{
	struct pci_sim_vf_tty *vf = pci_get_drvdata(pdev);

	if (!vf)
		return;

	mutex_lock(&vf->state_lock);
	vf->dead = true;
	mutex_unlock(&vf->state_lock);

	tty_port_tty_hangup(&vf->port, false);
	tty_unregister_device(pci_sim_tty_driver, vf->id);
	pci_set_drvdata(pdev, NULL);
	pci_disable_device(pdev);
	tty_port_put(&vf->port);
}

static const struct pci_device_id pci_sim_vf_ids[] = {
	{ PCI_DEVICE(FAKE_PCI_VENDOR_ID, FAKE_PCI_VF_DEVICE_ID) },
	{}
};
MODULE_DEVICE_TABLE(pci, pci_sim_vf_ids);

struct pci_driver pci_sim_vf_driver = {
	.name = "pci_sim_loopback_vf",
	.id_table = pci_sim_vf_ids,
	.probe = pci_sim_vf_probe,
	.remove = pci_sim_vf_remove,
};

/* TTY driver registration (called from core init/exit) */

int pci_sim_tty_register_driver(void)
{
	int ret;

	pci_sim_tty_driver =
		tty_alloc_driver(PCI_SIM_MAX_TTYS,
				 TTY_DRIVER_REAL_RAW | TTY_DRIVER_DYNAMIC_DEV);
	if (IS_ERR(pci_sim_tty_driver))
		return PTR_ERR(pci_sim_tty_driver);

	pci_sim_tty_driver->driver_name = "pci_sim_loopback";
	pci_sim_tty_driver->name = PCI_SIM_TTY_NAME;
	pci_sim_tty_driver->major = 0;
	pci_sim_tty_driver->minor_start = 0;
	pci_sim_tty_driver->type = TTY_DRIVER_TYPE_SERIAL;
	pci_sim_tty_driver->subtype = SERIAL_TYPE_NORMAL;
	pci_sim_tty_driver->init_termios = tty_std_termios;
	pci_sim_tty_driver->init_termios.c_cflag = B9600 | CS8 | CREAD | HUPCL |
						   CLOCAL;
	pci_sim_tty_driver->init_termios.c_lflag &= ~(ECHO | ICANON);
	pci_sim_tty_driver->init_termios.c_oflag &= ~(OPOST | ONLCR);

	tty_set_operations(pci_sim_tty_driver, &pci_sim_tty_ops);

	ret = tty_register_driver(pci_sim_tty_driver);
	if (ret) {
		tty_driver_kref_put(pci_sim_tty_driver);
		pci_sim_tty_driver = NULL;
	}

	return ret;
}

void pci_sim_tty_unregister_driver(void)
{
	if (!pci_sim_tty_driver)
		return;

	tty_unregister_driver(pci_sim_tty_driver);
	tty_driver_kref_put(pci_sim_tty_driver);
	pci_sim_tty_driver = NULL;
	xa_destroy(&pci_sim_tty_xa);
}
