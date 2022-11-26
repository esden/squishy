# SPDX-License-Identifier: BSD-3-Clause

from typing import (
	Dict, Any
)

from torii  import (
	Elaboratable, Module
)

__doc__ = '''\

'''

__all__ = (
	'Rev2USB',
)


class Rev2USB(Elaboratable):
	def __init__(self, *, config: Dict[str, Any]) -> None:
		self.config = config

	def elaborate(self, platform) -> Module:
		m = Module()


		return m
