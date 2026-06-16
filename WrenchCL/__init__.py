"""WrenchCL - Core functionality always available."""

from ._Internal import WrenchLogger

# noinspection PyUnusedFunction,PySameParameterValue
logger: WrenchLogger = WrenchLogger()

__all__ = ["logger"]
