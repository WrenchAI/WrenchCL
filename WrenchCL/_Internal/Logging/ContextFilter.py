#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
import logging
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .LoggerConfigState import LoggerStateManager


class ContextPrefixFilter(logging.Filter):
    """
    Logging filter that injects contextual prefix fields onto every LogRecord.

    Injected attributes:
      record.wrench_context       str   Pre-built bracket string "[run_id | ...]" or ""
      record.wrench_run_id        str   Run ID or "" when context is inactive
      record.wrench_prefix        str   User-set prefix or ""
      record.wrench_thread_name   str   Thread name or "" when show_thread_name is False
    """

    def __init__(self, state_manager: "LoggerStateManager") -> None:
        super().__init__()
        self._state_manager = state_manager

    def filter(self, record: logging.LogRecord) -> bool:
        state = self._state_manager.current_state

        if not state.should_show_env_prefix:
            record.wrench_context = ""
            record.wrench_run_id = ""
            record.wrench_prefix = ""
            record.wrench_thread_name = ""
            return True

        run_id: str = self._state_manager.run_id or ""
        prefix: str = state.log_prefix or ""
        thread_name: str = threading.current_thread().name if state.show_thread_name else ""
        logger_name: str = record.name or ""

        record.wrench_run_id = run_id
        record.wrench_prefix = prefix
        record.wrench_thread_name = thread_name

        parts = [p for p in (run_id, prefix, thread_name, logger_name) if p]

        record.wrench_context = ("[" + " | ".join(parts) + "] ") if parts else ""
        return True
