# SPDX-License-Identifier: BSD-3-Clause
from amaranth import *

__all__ = (
	'SPIInterface',
)

class SPIInterface(Elaboratable):
	'''Generic SPI interface

	'''
	def __init__(self):

		self._status_led = None
		self._spi = None

		self.cs   = Signal()
		self.xfr  = Signal()
		self.done = Signal()
		self.wdat = Signal(8)
		self.rdat = Signal(8)

	def elaborate(self, platform):
		self._spi = platform.request('spi_flash_1x')

		m = Module()

		bit = Signal(range(8))
		clk = Signal(reset = 1)

		cipo = self._spi.cipo.i
		copi = self._spi.copi.o

		d_in  = Signal.like(self.rdat)
		d_out = Signal.like(self.wdat)

		m.d.comb += self.done.eq(0)

		with m.FSM(name = 'spi'):
			with m.State('IDLE'):
				m.d.sync += clk.eq(1)
				with m.If(self.xfr):
					m.d.sync += d_out.eq(self.wdat)
					m.next = 'XFR'
			with m.State('XFR'):
				with m.If(clk):
					m.d.sync += [
						clk.eq(0),
						bit.eq(bit + 1),
						copi.eq(d_out[7]),
					]
				with m.Else():
					m.d.sync += [
						clk.eq(1),
						d_out.eq(d_out.shift_left(1)),
						d_in.eq(Cat(cipo, d_in[:-1])),
					]
					with m.If(bit == 0):
						m.next = 'DONE'
			with m.State('DONE'):
				m.d.comb += self.done.eq(1)
				m.d.sync += self.rdat.eq(d_in)
				with m.If(self.xfr):
					m.d.sync += d_out.eq(self.wdat)
					m.next = 'XFR'
				with m.Else():
					m.next = 'IDLE'

		m.d.comb += [
			self._spi.clk.o.eq(clk),
			self._spi.cs_n.o.eq(self.cs),
		]

		return m
