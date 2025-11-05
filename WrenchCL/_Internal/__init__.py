"""Internal utilities - some require AWS dependencies."""

# Always available
from ._MockPandas import pd
from .cLogger import cLogger

__all__ = [
        'pd',
        "cLogger"
        ]
