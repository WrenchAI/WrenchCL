from .Tools.WrenchLogger import Logger

# Assign the deprecated_logger to the name 'logger' for backward compatibility
logger = Logger()

__all__ = ['logger', 'Logger']
