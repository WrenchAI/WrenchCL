"""WrenchCL - Core functionality always available."""

from typing import Any

from ._Internal import WrenchLogger

# noinspection PyUnusedFunction,PySameParameterValue
logger: Any = WrenchLogger()

__all__ = ["logger"]
