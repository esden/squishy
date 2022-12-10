# SPDX-License-Identifier: BSD-3-Clause
from typing                              import (
	Tuple, Union
)
from torii                               import (
	Record
)
from torii.hdl.rec                       import (
	DIR_FANIN, DIR_FANOUT
)
from torii.sim                           import (
	Settle
)
from usb_construct.types                 import (
	USBRequestType,
)
from usb_construct.types.descriptors.dfu import (
	DFURequests
)
from gateware_test                       import (
	SquishyUSBGatewareTestCase, sim_test
)
from squishy.core.flash                  import (
	FlashGeometry
)

from squishy.gateware.bootloader.dfu     import (
	DFURequestHandler, DFUState
)

_DFU_DATA = (
	0xff, 0x00, 0x00, 0xff, 0x7e, 0xaa, 0x99, 0x7e, 0x51, 0x00, 0x01, 0x05, 0x92, 0x00, 0x20, 0x62,
	0x03, 0x67, 0x72, 0x01, 0x10, 0x82, 0x00, 0x00, 0x11, 0x00, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
)

_SPI_RECORD = Record((
	('clk', [
		('o', 1, DIR_FANOUT),
	]),
	('cs', [
		('o', 1, DIR_FANOUT),
	]),
	('copi', [
		('o', 1, DIR_FANOUT),
	]),
	('cipo', [
		('i', 1, DIR_FANIN),
	]),
))

class DFUPlatform:
	flash = {
		'geometry': FlashGeometry(
			size       = 8388608, # 8MiB
			page_size  = 256,
			erase_size = 4096,    # 4KiB
			addr_width = 24
		).init_slots(device = 'iCE40HX8K'),
		'commands': {
			'erase': 0x20,
		}
	}

	def request(self, name, number):
		return _SPI_RECORD


class DFURequestHandlerTests(SquishyUSBGatewareTestCase):
	dut: DFURequestHandler = DFURequestHandler
	dut_args = {
		'configuration': 1,
		'interface': 0,
		'resource_name': ('spi_flash_x1', 0)
	}
	domains = (('usb', 60e6),)
	platform = DFUPlatform()

	def sendDFUDetach(self):
		yield from self.sendSetup(type = USBRequestType.CLASS, retrieve = False,
			req = DFURequests.DETACH, value = 1000, index = 0, length = 0)

	def sendDFUDownload(self):
		yield from self.sendSetup(type = USBRequestType.CLASS, retrieve = False,
			req = DFURequests.DOWNLOAD, value = 0, index = 0, length = 256)

	def sendDFUGetStatus(self):
		yield from self.sendSetup(type = USBRequestType.CLASS, retrieve = True,
			req = DFURequests.GET_STATUS, value = 0, index = 0, length = 6)

	def sendDFUGetState(self):
		yield from self.sendSetup(type = USBRequestType.CLASS, retrieve = True,
			req = DFURequests.GET_STATE, value = 0, index = 0, length = 1)


	@sim_test(domain = 'usb')
	def test_dfu_handler(self):
		yield self.dut.interface.active_config.eq(1)
		yield Settle()
		yield from self.step(2)
		yield from self.wait_until_low(_SPI_RECORD.cs.o)
		yield from self.step(2)
		yield from self.sendDFUGetStatus()
		yield from self.receiveData(data = (0, 0, 0, 0, DFUState.Idle, 0))
		yield from self.sendSetupSetInterface()
		yield from self.receiveZLP()
		yield from self.step(3)
		yield from self.sendDFUDownload()
		yield from self.sendData(data = _DFU_DATA)
		yield from self.sendDFUGetStatus()
		yield from self.receiveData(data = (0, 0, 0, 0, DFUState.DlBusy, 0))
		yield from self.sendDFUGetState()
		yield from self.receiveData(data = (DFUState.DlBusy, ))
		yield from self.step(6)
		yield from self.sendDFUGetState()
		# Keep checking for Download Busy
		while (yield from self.receiveData(data = (DFUState.DlBusy, ), check = False)):
			yield from self.sendDFUGetState()
		yield from self.sendDFUGetState()
		yield from self.receiveData(data = (DFUState.DlSync,))
		yield from self.sendDFUGetStatus()
		yield from self.receiveData(data = (0, 0, 0, 0, DFUState.DlSync, 0))
		yield from self.sendDFUGetState()
		yield from self.receiveData(data = (DFUState.DlIdle,))
		yield
		yield from self.sendDFUDetach()
		yield from self.receiveZLP()
		self.assertEqual((yield self.dut.triggerReboot), 1)
		yield Settle()
		yield
		self.assertEqual((yield self.dut.triggerReboot), 1)
		yield
