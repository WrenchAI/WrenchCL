"""WrenchCL - Core functionality always available."""
from ._Internal import cLogger

# noinspection PyUnusedFunction,PySameParameterValue
logger: cLogger = cLogger()

__all__ = ['logger']
