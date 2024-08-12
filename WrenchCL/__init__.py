import warnings
from .Tools.WrenchLogger import Logger

# Check if 'logger' has been imported from 'WrenchCL.Tools.WrenchLogger'
try:
    from .Tools.WrenchLogger import logger
    # If 'logger' is imported, issue a warning and reassign
    warnings.warn(
        "The pre-instantiated 'logger' object is deprecated and will be removed in a future release. Please use from' WrenchCL import Logger' instead and instantiate.",
        DeprecationWarning,
        stacklevel=2
    )
except ImportError:
    # 'logger' is not imported; nothing to do here
    pass

# Create a new instance of Logger and assign it to `logger`
logger = Logger()

__all__ = [
    'logger', 'Logger'
]
