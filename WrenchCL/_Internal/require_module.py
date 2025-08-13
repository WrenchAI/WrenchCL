#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
import warnings
from typing import List, Optional, Union


def gate_imports(imports_passed: bool, extra: str, package: Optional[Union[str, List[str]]] = None, raise_exc: bool = True):
    from WrenchCL.Tools.ccLogBase import logger

    if imports_passed:
        return

    if package is not None:
        if isinstance(package, str):
            error_string = f"Missing optional dependency: {package}"
        else:
            error_string = f"Missing optional dependencies: {', '.join(package)}"
    else:
        error_string = f"Missing optional dependency."

    error_string += f"\nInstall with: pip install 'WrenchCL[{extra}]'"

    if raise_exc:
        e = ImportError(error_string)
        logger.error(e,)
        raise e
    else:
        # Force warning visibility and fallback to logger if needed
        try:
            warnings.warn(error_string, category=ImportWarning, stacklevel=2)
        except Warning as w:
            logger.warning(f"Suppressed warning: {error_string}")