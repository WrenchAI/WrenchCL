"""
BaseLogger - Core logging interface for WrenchCL
"""
#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

import threading
from contextlib import contextmanager
from typing import Optional, Literal, Any, Union

from .internal_api import InternalAPI
from ..DataClasses import LogLevel, LogOptions, logLevels


class BaseLogger:
    """Core logging interface with structured, colorized output"""

    def __init__(self):
        self._lock = threading.RLock()
        self._internal = InternalAPI(self)
        # Will be initialized by cLogger
        self.state_manager = None

    def info(
            self, *args: Any, header: Optional[str] = None,
            log_opts: Optional[Union[LogOptions, dict]] = None
            ) -> None:
        """Log an INFO-level message"""
        opts = LogOptions(log_opts)
        self._log(level="INFO", args=args, no_format=opts.no_format,
                  no_color=opts.no_color, stack_info=opts.stack_info, header=header)

    def debug(self, *args: Any, log_opts: Optional[Union[LogOptions, dict]] = None) -> None:
        """Log a DEBUG-level message"""
        opts = LogOptions(log_opts)
        self._log(level="DEBUG", args=args, no_format=opts.no_format,
                  no_color=opts.no_color, stack_info=opts.stack_info)

    def warning(
            self, *args: Any, header: Optional[str] = None,
            log_opts: Optional[Union[LogOptions, dict]] = None, **kwargs
            ) -> None:
        """Log a WARNING-level message"""
        opts = LogOptions(log_opts)
        if isinstance(kwargs.get('exc_info', ''), (Exception, BaseException)):
            args = args + (kwargs.get('exc_info'),)
        self._log(level="WARNING", args=args, no_format=opts.no_format,
                  no_color=opts.no_color, stack_info=opts.stack_info, header=header)

    def error(
            self, *args: Any, header: Optional[str] = None,
            log_opts: Optional[Union[LogOptions, dict]] = None, **kwargs: Any
            ) -> None:
        """Log an ERROR-level message"""
        if log_opts is None:
            log_opts = LogOptions()
        elif isinstance(log_opts, dict):
            log_opts = LogOptions(**log_opts)
        if isinstance(kwargs.get('exc_info', ''), (Exception, BaseException)):
            args = args + (kwargs.get('exc_info'),)
        self._log(level="ERROR", args=args, no_format=log_opts.no_format,
                  no_color=log_opts.no_color, stack_info=log_opts.stack_info, header=header)

    def critical(
            self, *args: Any, header: Optional[str] = None,
            log_opts: Optional[Union[LogOptions, dict]] = None, **kwargs: Any
            ) -> None:
        """Log a CRITICAL-level message"""
        if log_opts is None:
            log_opts = LogOptions()
        elif isinstance(log_opts, dict):
            log_opts = LogOptions(**log_opts)
        if isinstance(kwargs.get('exc_info', ''), (Exception, BaseException)):
            args = args + (kwargs.get('exc_info'),)
        self._log(level="CRITICAL", args=args, no_format=log_opts.no_format,
                  no_color=log_opts.no_color, stack_info=log_opts.stack_info, header=header)

    def exception(
            self, *args: Any, header: Optional[str] = None,
            log_opts: Optional[Union[LogOptions, dict]] = None, **kwargs
            ) -> None:
        """Log an ERROR-level message with exception context"""
        opts = LogOptions(log_opts)
        if isinstance(kwargs.get('exc_info', ''), (Exception, BaseException)):
            args = args + (kwargs.get('exc_info'),)
        self._log(level="ERROR", args=args, no_format=opts.no_format,
                  no_color=opts.no_color, stack_info=opts.stack_info, header=header)

    def success(
            self, *args: Any, header: Optional[str] = None,
            log_opts: Optional[Union[LogOptions, dict]] = None
            ) -> None:
        """Log a success message (alias for info)"""
        self.info(*args, header=header, log_opts=log_opts)

    def configure(
            self, mode: Optional[Literal['terminal', 'json', 'compact']] = None,
            level: Optional[logLevels] = None, color_enabled: Optional[bool] = None,
            highlight_syntax: Optional[bool] = None, verbose: Optional[bool] = None,
            trace_enabled: Optional[bool] = None, deployment_mode: Optional[bool] = None,
            suppress_autoconfig: bool = True
            ) -> None:
        """Configure logger behavior and settings"""
        if trace_enabled is not None:
            self._internal.setup_ddtrace(trace_enabled)

        self.state_manager.handler_manager.flush_all_handlers()
        new_config = self.state_manager.configure(
                mode=mode, level=level, color_enabled=color_enabled,
                highlight_syntax=highlight_syntax, verbose=verbose,
                trace_enabled=trace_enabled, deployment_mode=deployment_mode,
                suppress_autoconfig=suppress_autoconfig
                )
        self.level = new_config.level

    def reinitialize(self, verbose=False):
        """Reload environment configuration and update logger settings"""
        self.state_manager.reinitialize()
        if verbose:
            import json
            self._internal.log_internal(json.dumps(self.state, indent=2, default=lambda x: str(x), ensure_ascii=False))

    def initiate_new_run(self):
        """Generate and assign a new run ID for process tracking"""
        with self._lock:
            self.state_manager.set_new_run_id()

    def header(
            self, text: str, size: int = None, compact=False,
            return_repr=False, level: logLevels = 'HEADER'
            ):
        """Create and log a formatted header"""
        config = self.state_manager.current_state
        compact = compact or config.is_compact_header_mode

        result = self.state_manager.message_processor.create_header(
                text, level=level, size=size, compact=compact
                )

        if not return_repr:
            self._log(level, args=(result,), no_format=True, no_color=True)
        else:
            return result

    def data(self, obj: Any, compact: bool = False, **kwargs) -> None:
        """Log objects in a visually formatted manner"""
        self._pretty_log(obj, compact=compact, **kwargs)

    def cdata(self, data: Any, **kwargs) -> None:
        """Log data in compact format"""
        self._pretty_log(data, compact=True, **kwargs)

    def add_file(
            self, filename: str, max_bytes: int = 10485760, backup_count: int = 5,
            level: logLevels = None, formatter=None
            ):
        """Add a rotating file handler for log output"""
        handler = self.state_manager.handler_manager.add_file_handler(
                filename=filename, config=self.state_manager.current_state,
                max_bytes=max_bytes, backup_count=backup_count, level=level,
                formatter=formatter, base_level=self.state_manager.base_level
                )
        self._internal.log_internal(f"File handler added: {filename}")
        return handler

    def flush(self):
        """Flush all logger handlers"""
        self.state_manager.handler_manager.flush_all_handlers()

    def close(self):
        """Close all handlers and clean up resources"""
        self.state_manager.handler_manager.close_all_handlers()
        self.state_manager.global_logger_manager.cleanup_global_handlers()

    @contextmanager
    def temporary(
            self, level: Optional[logLevels] = None,
            mode: Optional[Literal['terminal', 'json', 'compact']] = None,
            color_enabled: Optional[bool] = None, verbose: Optional[bool] = None,
            trace_enabled: Optional[bool] = None, highlight_syntax: Optional[bool] = None,
            deployed: Optional[bool] = None
            ):
        """Temporarily override logger configuration within a context"""
        overrides = {}
        if level is not None:
            overrides['level'] = LogLevel(level)
        if mode is not None:
            overrides['mode'] = mode
            if mode == 'json' and deployed is None:
                overrides['deployed'] = True
        if color_enabled is not None:
            overrides['color_enabled'] = color_enabled
        if verbose is not None:
            overrides['verbose'] = verbose
        if trace_enabled is not None:
            overrides['dd_trace_enabled'] = trace_enabled
        if highlight_syntax is not None:
            overrides['highlight_syntax'] = highlight_syntax
        if deployed is not None:
            overrides['deployed'] = deployed

        temp_state = self.state_manager.create_temporary_state(**overrides)
        old_state = self.state_manager.apply_temporary_state(temp_state)

        if level is not None:
            with self._lock:
                self.state_manager.handler_manager.flush_all_handlers()
                self.state_manager.logging_instance.setLevel(int(LogLevel(level)))

        try:
            yield
        finally:
            self.state_manager.restore_state(old_state)

    @property
    def level(self) -> LogLevel:
        """Current logging level"""
        import logging
        return LogLevel(logging.getLevelName(self.state_manager.logging_instance.level))

    @level.setter
    def level(self, level: LogLevel):
        try:
            level = LogLevel(level)
            self.state_manager.configure(level=level)
        except Exception as e:
            self._internal.log_internal(f"Failed to set logger level: {e}")

    @property
    def mode(self) -> str:
        """Current logging mode"""
        return self.state_manager.current_state.mode

    @property
    def state(self) -> dict:
        """Complete logger state information"""
        config = self.state_manager.current_state
        env_metadata = self.state_manager.get_env_metadata()

        return {
                "Logging Level": self.level.value,
                "Run Id": self.state_manager.run_id,
                "Mode": config.mode,
                "Environment Metadata": env_metadata,
                "Configuration": {
                        "Color Enabled": config.color_enabled,
                        "Highlight Syntax": config.highlight_syntax,
                        "Verbose": config.verbose,
                        "Deployment Mode": config.deployed,
                        "DD Trace Enabled": config.dd_trace_enabled,
                        "Global Stream Configured": self.state_manager.global_stream_configured
                        },
                "Handlers": [type(h).__name__ for h in self.state_manager.logging_instance.handlers],
                }

    @property
    def run_id(self) -> str:
        """Current run ID"""
        return self.state_manager.run_id

    def _log(
            self, level: Union[LogLevel, logLevels], args,
            no_format: bool = False, no_color: bool = False,
            stack_info: bool = False, header: Optional[str] = None
            ) -> None:
        """Core logging method"""
        if not isinstance(level, LogLevel):
            level = LogLevel(level)

        config = self.state_manager.current_state

        msg, exc_info = self.state_manager.message_processor.process_log_message(
                level, args, config, header, no_color
                )

        if level not in ['ERROR', 'CRITICAL'] and not stack_info:
            exc_info = None

        with self._lock:
            self.state_manager.handler_manager.flush_all_handlers()
            self._internal.update_formatters(level, no_format, no_color)

        if config.should_format_message(no_format):
            if len(msg.strip().splitlines()) > 1 and not msg.startswith('\n'):
                msg = '\n' + msg

        from ..logging_utils import get_depth
        self.state_manager.logging_instance.log(
                int(level), msg, exc_info=exc_info, stack_info=stack_info,
                stacklevel=get_depth(internal=level == 'INTERNAL')
                )

    def _pretty_log(self, obj: Any, compact: bool = False, **kwargs) -> None:
        """Log objects in a visually formatted manner"""
        from ..logging_utils import ensure_str
        from ... import pd
        import json
        from pprint import pformat

        obj = ensure_str(obj)
        output = obj
        config = self.state_manager.current_state
        cwidth = kwargs.get('cwidth', 240)
        indent = kwargs.get('indent', 2)

        try:
            if isinstance(obj, pd.DataFrame):
                prefix_str = f"DataType: {type(obj).__name__} | Shape: {obj.shape[0]} rows | {obj.shape[1]} columns"
                pd.set_option('display.max_rows', 500, 'display.max_columns', None,
                              'display.width', None, 'display.max_colwidth', 50,
                              'display.colheader_justify', 'center')
                if config.mode != 'json':
                    output = f"{prefix_str}\n{obj}"
                else:
                    output = obj.to_json(orient='records', indent=indent, **kwargs)
            elif isinstance(obj, dict):
                output = json.dumps(obj, indent=indent, ensure_ascii=False, **kwargs) if not compact else pformat(obj, compact=True, width=cwidth)
            elif hasattr(obj, 'model_dump_json'):
                output = obj.model_dump_json(indent=indent, **kwargs)
            elif hasattr(obj, 'dump_json_schema'):
                output = obj.dump_json_schema(indent=indent, **kwargs)
            elif hasattr(obj, 'pretty_repr'):
                output = obj.pretty_repr(**kwargs)
            elif hasattr(obj, 'json'):
                raw = obj.json()
                output = json.dumps(raw, indent=indent, ensure_ascii=False, **kwargs) if not compact else pformat(raw, compact=compact, width=cwidth)
            elif isinstance(obj, str) or hasattr(obj, '__repr__') or hasattr(obj, '__str__'):
                try:
                    parsed = json.loads(obj)
                    output = json.dumps(parsed, indent=indent, ensure_ascii=False, default=str, **kwargs) if not compact else pformat(parsed, compact=True, width=cwidth)
                except Exception:
                    output = obj
            elif hasattr(obj, '__dict__'):
                raw = str(obj.__dict__)
                output = json.dumps(raw, indent=indent, ensure_ascii=False, **kwargs) if not compact else pformat(raw, compact=compact, width=cwidth)
            else:
                output = pformat(obj, compact=compact, width=cwidth)
        except Exception:
            output = obj
        finally:
            if isinstance(output, str):
                output = output.strip()
        self._log("DATA", args=(output,))
