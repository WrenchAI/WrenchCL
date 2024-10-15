import warnings
import inspect
from .WrenchLogger import Logger

# Inspect the stack to see how the module was imported
def check_import_usage():
    stack = inspect.stack()
    for frame in stack:
        # Check the source code in the current frame
        source_code = frame.code_context[0].strip() if frame.code_context else ""

        if "import logger" in source_code or "from WrenchCL import logger" in source_code:
            warnings.warn("Using the pre-instantiated 'logger' object is not-recommended due to implied settings being used."
                          "Please use 'from WrenchCL.Tools import Logger' or from 'WrenchCL import Logger' instead and instantiate it using logger = Logger().",
                          DeprecationWarning, stacklevel=3)


# Check for deprecated imports when the module is imported
# check_import_usage()

# Create a new instance of Logger and assign it to `logger`
logger = Logger()

from .Coalesce import *  # Import all symbols from Coalesce
from .FetchMetaData import *  # Import all symbols from FetchMetaData
from .FileTyper import *  # Import all symbols from FileTyper
from .Image2B64 import *  # Import all symbols from Image2B64
from .JsonSerializer import *  # Import all symbols from JsonSerializer
from .MaybeMonad import *  # Import all symbols from MaybeMonad
from .TypeChecker import *  # Import all symbols from TypeChecker

__all__ = ['coalesce', 'get_file_type', 'image_to_base64', 'Maybe', 'logger',  # Ensure `logger` is included here
           'Logger', 'typechecker', 'get_metadata', 'robust_serializer', 'validate_base64', 'single_quote_decoder']
