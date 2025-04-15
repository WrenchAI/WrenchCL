from typing import Type

from .Tools.WrenchLogger import _IntLogger


logger: _IntLogger = _IntLogger()
Logger: _IntLogger = _IntLogger()
ext_logger: Type[_IntLogger] = _IntLogger

__all__ = ['logger', 'Logger', 'ext_logger']
