"""
Example usage of the refactored WrenchCL logger API
"""

#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

import logging
import sys

from WrenchCL import logger


def main():
    # Core logging operations - unchanged from before
    logger.info("Application starting up")
    logger.configure(mode="terminal", level="DEBUG", color_enabled=True)
    logger.debug("Debug information")
    logger.error("An error occurred", exc_info=Exception("Test error"))

    # Pretty print data
    logger.data({"key": "value", "numbers": [1, 2, 3]})
    logger.cdata({"compact": True})  # compact format

    # File output - simplified from enable_file_logging
    logger.add_file("app.log", max_bytes=5 * 1024 * 1024)  # 5MB

    # Stream output - simplified from add_new_handler
    logger.add_stream(stream=sys.stderr, level="WARNING")

    # Instance management - managing this logger's handlers
    custom_handler = logging.FileHandler("custom.log")
    logger.managed.add(logging.StreamHandler, stream=sys.stdout, owned=True)
    logger.managed.adopt(custom_handler, preserve_formatter=True)
    logger.managed.sync()  # sync all handler levels

    # Silence other loggers
    logger.managed.silence(['requests', 'urllib3', 'boto3'])
    logger.managed.silence('all')  # silence everything except WrenchCL
    logger.managed.set_level('my_package', 'WARNING')

    # Stream/system management - controlling entire logging system
    logger.streams.attach(level="INFO", silence_others=True)
    logger.streams.intercept_exceptions(install_hooks=True, std_stream_mode="stderr")
    logger.streams.suppress("both")  # suppress stdout/stderr
    logger.streams.force_markup()  # force colors even in non-terminal

    # Temporary configuration
    with logger.temporary(mode="json", level="ERROR"):
        logger.info("This will be in JSON format at ERROR level")

    # Cleanup
    logger.flush()
    logger.close()


if __name__ == "__main__":
    main()
