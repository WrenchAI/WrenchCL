"""WrenchCL - Core functionality always available."""
from .cLogger import cLogger

# noinspection PyUnusedFunction,PySameParameterValue
logger: cLogger = cLogger()

__all__ = ['logger']
