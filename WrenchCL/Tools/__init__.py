import warnings
from .Coalesce import *  # Import all symbols from Coalesce
from .FetchMetaData import *  # Import all symbols from FetchMetaData
from .FileTyper import *  # Import all symbols from FileTyper
from .Image2B64 import *  # Import all symbols from Image2B64
from .JsonSerializer import *  # Import all symbols from JsonSerializer
from .MaybeMonad import *  # Import all symbols from MaybeMonad
from .TypeChecker import *  # Import all symbols from TypeChecker
from .WrenchLogger import Logger

# Try importing 'logger' from WrenchLogger and issue a warning if present
try:
    from .WrenchLogger import logger
    warnings.warn(
        "The pre-instantiated 'logger' object is deprecated and will be removed in a future release. Please use from' WrenchCL.Tools import Logger' instead and instantiate",
        DeprecationWarning,
        stacklevel=2
    )
except ImportError:
    # 'logger' is not imported; nothing to do here
    pass

# Create a new instance of Logger and assign it to `logger`
logger = Logger()

__all__ = [
    'coalesce',
    'get_file_type',
    'image_to_base64',
    'Maybe',
    'logger',  # Make sure `logger` is included here
    'Logger',
    'typechecker',
    'get_metadata',
    'robust_serializer',
    'validate_base64',
    'single_quote_decoder'
]
