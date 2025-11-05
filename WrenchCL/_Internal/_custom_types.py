#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
from enum import Enum


class StdStreamMode(str, Enum):
    NONE = "none"
    STDERR = "stderr"
    BOTH = "both"
