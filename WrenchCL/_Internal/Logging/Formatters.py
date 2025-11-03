#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
import contextvars
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Final

from .ColorService import ColorService, ColorPresets, MockColorama
from .DataClasses import logLevels, LogLevel


class CustomFormatter(logging.Formatter):
    def __init__(self, fmt: str, datefmt: Optional[str], presets: ColorPresets):
        super().__init__(fmt, datefmt)
        self.presets = presets

    def formatStack(self, exc_info: str) -> str:
        dim_color = self.presets._INTERNAL_DIM_COLOR or ''
        dim_style = self.presets._INTERNAL_DIM_STYLE or ''
        reset = self.presets.RESET or ''
        return f"{dim_color}{dim_style}{exc_info}{reset}"

    def formatException(self, ei) -> str:
        original = super().formatException(ei)
        dim_color = self.presets._INTERNAL_DIM_COLOR or ''
        dim_style = self.presets._INTERNAL_DIM_STYLE or ''
        reset = self.presets.RESET or ''
        return f"{dim_color}{dim_style}{original}{reset}"


class JSONLogFormatter(logging.Formatter):
    """
    Datadog-friendly JSON formatter that preserves existing structure and features.

    Top-level fields (for Datadog correlation & triad):
      - ``service``, ``env``, ``version``
      - ``dd.trace_id``, ``dd.span_id``

    Preserved blocks:
      - ``source``: module/function/line (unchanged)
      - ``log_info``: logger/timestamp (unchanged)
      - ``context``: harvested hints (unchanged)
      - ``exception``: formatted tracebacks (unchanged)

    Parameters
    ----------
    env_metadata : Dict[str, Optional[str]]
        Expected keys: ``env``, ``project`` (service), ``project_version``.
    forced_color : bool
        If True and not ``deployed``, apply highlight function to the JSON string.
    highlight_func : Callable[[str], str]
        Function that colorizes the JSON string for terminals.
    traced : bool
        Kept for compatibility; IDs come from a filter, but we still surface them.
    deployed : bool
        If True, emit single-line compact JSON (for log routers).
    """

    # Constants (no behavior change)
    _TIMEFMT: Final[str] = "%Y-%m-%dT%H:%M:%S.%fZ"

    def __init__(
        self,
        env_metadata: Dict[str, Optional[str]],
        forced_color: bool,
        highlight_func: Callable[[str], str],
        traced: bool = False,
        deployed: bool = False
    ) -> None:
        super().__init__()
        self.env_metadata = env_metadata
        self.color_mode = forced_color
        self.highlight_func = highlight_func
        self.traced = traced
        self.deployed = deployed

    # ---------- context harvesting (same spirit, preserved) ----------
    @staticmethod
    def _extract_generic_context() -> Dict[str, Any]:
        """
        Safely extract recognized context keys (user/org/service) from contextvars,
        handling both dicts and __dict__-bearing objects, even if cyclic.
        """
        context_data: Dict[str, Any] = {}

        user_keys = {
            "user_id", "usr_id", "entity_id", "user_entity_id", "subject_id",
            "client_id", "user_name", "username",
        }
        org_keys = {"client_id", "org_id", "organization_id", "tenant_id", "team_id", "workspace_id", "project_id"}
        svc_keys = {"service_id", "service_name", "application", "app_name", "dd_service",
                    "aws_function_name", "aws_service", "lambda_name", "lambda_function",
                    "aws_function", "project_name", "project"}

        def add(k: str, v: Any) -> None:
            lk = (k or "").lower()
            if lk in user_keys:
                context_data.setdefault("user_id", v)
            elif lk in org_keys:
                context_data.setdefault("organization_id", v)
            elif lk in svc_keys:
                context_data.setdefault("service_name", v)

        visited: set[int] = set()

        def inspect_obj(obj: Any) -> None:
            """Shallow inspection of dicts or objects with __dict__, avoiding recursion."""
            obj_id = id(obj)
            if obj_id in visited:
                return
            visited.add(obj_id)

            if isinstance(obj, dict):
                for k, v in list(obj.items())[:20]:
                    if id(v) == obj_id:
                        continue
                    add(k, v)
                    if isinstance(v, (dict, object)) and not isinstance(v, (str, int, float, bool, type(None))):
                        # Shallowly inspect children once
                        inspect_obj(getattr(v, "__dict__", None) or {})
            else:
                d = getattr(obj, "__dict__", None)
                if isinstance(d, dict):
                    for k, v in list(d.items())[:20]:
                        if id(v) == obj_id:
                            continue
                        add(k, v)
                        if isinstance(v, (dict, object)) and not isinstance(v, (str, int, float, bool, type(None))):
                            inspect_obj(getattr(v, "__dict__", None) or {})

        try:
            ctx = contextvars.copy_context()
            for var in ctx:
                try:
                    val = ctx.get(var)
                    inspect_obj(val)
                except RecursionError:
                    continue
                except Exception:
                    continue
        except Exception:
            pass

        return context_data



    def _formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        """
        Formats the record creation time safely.

        Falls back to ISO 8601 UTC timestamp if the given datefmt is invalid.
        """
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)

        # Try the provided format first
        if datefmt:
            try:
                return dt.strftime(datefmt)
            except ValueError:
                # Fallback to a portable ISO format
                return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")

        # No datefmt provided → use ISO format
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    # ------------------------------- core -------------------------------
    def format(self, record: logging.LogRecord) -> str:
        # Resolve triad from env_metadata first, then DD_* fallbacks
        service = (
            self.env_metadata.get("project")
            or os.getenv("DD_SERVICE")
            or os.getenv("PROJECT_NAME")
            or "unknown-service"
        )
        env = (
            self.env_metadata.get("env")
            or os.getenv("DD_ENV")
            or os.getenv("ENV")
            or "dev"
        )
        version = (
            self.env_metadata.get("project_version")
            or os.getenv("DD_VERSION")
            or os.getenv("REPO_VERSION")
            or "0.0.0"
        )

        # Correlation IDs injected by DatadogTraceInjectionFilter (decimal strings)
        dd_trace_id = str(getattr(record, "dd.trace_id", "0"))
        dd_span_id = str(getattr(record, "dd.span_id", "0"))

        # Base payload — keeps your original structure
        log_record: Dict[str, Any] = {
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "timestamp": self._formatTime(record, self._TIMEFMT),
        }
        if self.traced:
            log_record.update({
                    "service": service,
                    "env": env,
                    "version": version,
                    "dd.trace_id": dd_trace_id,
                    "dd.span_id": dd_span_id,
                    "logger": record.name,
                    })


        # Context (preserved)
        ctx = self._extract_generic_context()
        if ctx:
            log_record["context"] = ctx

        # Exceptions (preserved)
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        # Output formatting (preserved behavior)
        dumped = (
            json.dumps(log_record, default=str, ensure_ascii=False)
            if self.deployed
            else json.dumps(log_record, default=str, ensure_ascii=False, indent=2)
        )
        if self.color_mode and not self.deployed:
            dumped = self.highlight_func(dumped)
        return dumped



class FileLogFormatter(logging.Formatter):
    def __init__(self, base_formatter: logging.Formatter):
        super().__init__(base_formatter._fmt, base_formatter.datefmt)
        self._base_formatter = base_formatter

    def format(self, record: logging.LogRecord) -> str:
        raw = self._base_formatter.format(record)
        from .logging_utils import remove_ansi
        return remove_ansi(raw)


class FormatterFactory:
    """
    Creates appropriate formatters based on configuration state.

    This factory encapsulates all the complex formatter creation logic
    that was previously scattered throughout cLogger.
    """
    from .ColorService import ColorService

    def __init__(self, color_service: ColorService):
        self.color_service = color_service
        self.env_prefix_generator = EnvPrefixGenerator(color_service)

    def create_formatter(
            self,
            level: logLevels,
            config_state,
            env_metadata: Dict,
            global_stream_configured: bool = False,
            no_format: bool = False,
            no_color: bool = False
            ) -> logging.Formatter:
        """
        Create appropriate formatter based on level and configuration.

        This replaces the complex __get_formatter method from cLogger.
        """

        if not isinstance(level, LogLevel):
            level = LogLevel(level)

        # Simple cases first
        if no_format and no_color:
            return logging.Formatter(fmt='%(message)s')
        # Determine active presets
        active_preset = self.color_service.get_current_presets()
        if not config_state.should_use_color(no_color):
            # Create mock presets for this formatter
            active_preset = ColorPresets(MockColorama, MockColorama)
        # JSON formatter case
        if config_state.should_use_json_formatter and level != 'INTERNAL':
            return JSONLogFormatter(
                    env_metadata,
                    config_state.force_markup,
                    self._get_highlight_function(),  # We'll need to inject this
                    config_state.should_enable_dd_trace_logging,
                    config_state.deployed
                    )

        # Terminal formatter case
        return self._create_terminal_formatter(
                LogLevel(level), config_state, env_metadata, active_preset,
                global_stream_configured, no_format
                )

    def _create_terminal_formatter(
            self, level: LogLevel, config_state,
            env_metadata: Dict, active_preset: ColorPresets,
            global_stream_configured: bool, no_format: bool
            ) -> CustomFormatter:
        """Create a terminal formatter with all the styling."""

        # Get colors and styles for this level
        color = active_preset.get_color_by_level(level)
        style = active_preset.get_level_style(level)
        message_color = active_preset.get_message_color(level)
        # Determine dimmed colors
        if level in ['ERROR', 'CRITICAL', 'WARNING']:
            dimmed_color = active_preset.get_color_by_level(level)
        else:
            dimmed_color = active_preset.get_color_by_level(LogLevel('INTERNAL'))

        dimmed_style = active_preset.get_level_style(LogLevel('INTERNAL'))

        # Special handling for INTERNAL level
        if level == 'INTERNAL':
            color = active_preset.CRITICAL
            style = active_preset.get_level_style(LogLevel('INTERNAL'))

        # Build format components
        components = self._build_format_components(
                LogLevel(level), config_state, env_metadata, active_preset,
                color, style, message_color, dimmed_color, dimmed_style,
                global_stream_configured, no_format
                )

        # Assemble final format
        fmt = f"{active_preset.RESET}{components['format']}{active_preset.RESET}"

        return CustomFormatter(fmt, datefmt='%H:%M:%S', presets=active_preset)

    def _build_format_components(
            self, level: LogLevel, config_state, env_metadata: Dict,
            active_preset: ColorPresets, color: str, style: str,
            message_color: str, dimmed_color: str, dimmed_style: str,
            global_stream_configured: bool, no_format: bool
            ) -> Dict[str, str]:
        """Build the various components of the log format string."""

        # File/function info section
        file_section = f"{dimmed_color}{dimmed_style}%(filename)s:%(funcName)s:%(lineno)d]{active_preset.RESET}"

        # Verbose timestamp section
        verbose_section = f"{dimmed_color}{dimmed_style}[%(asctime)s|{file_section}{active_preset.RESET}"

        # Environment prefix
        app_env_section = self.env_prefix_generator.generate_prefix(
                env_metadata, config_state, dimmed_color, dimmed_style, color, style
                )

        # Level name section
        level_name_section = self._get_level_name_section(level, color, style, active_preset)

        # Other sections
        colored_arrow_section = f"{color}{style} -> {active_preset.RESET}"
        if str(level) not in ['INTERNAL', 'DEBUG']:
            message_section = f"{style}{message_color}%(message)s{active_preset.RESET}"
        else:
            message_section = f"{dimmed_color}{dimmed_style}%(message)s{active_preset.RESET}"

        # Logger name section (for global streams)
        name_section = f"{color}{style}[%(name)s] - {active_preset.RESET}" if global_stream_configured else ""

        # Choose format based on mode and level
        if config_state.mode == 'compact':
            format_str = f"{level_name_section}{file_section}{colored_arrow_section}{message_section}"
        elif no_format:
            format_str = "%(message)s"
        elif level == 'INTERNAL':
            format_str = f"{level_name_section}{colored_arrow_section}{message_section}"
        else:
            format_str = f"{app_env_section}{name_section}{level_name_section}{verbose_section}{colored_arrow_section}{message_section}"

        return {
                'format': format_str,
                'file_section': file_section,
                'verbose_section': verbose_section,
                'app_env_section': app_env_section,
                'level_name_section': level_name_section,
                'colored_arrow_section': colored_arrow_section,
                'message_section': message_section,
                'name_section': name_section
                }

    def _get_level_name_section(
            self, level: LogLevel, color: str, style: str,
            active_preset: ColorPresets
            ) -> str:
        """Get the formatted level name section."""
        if level == "INTERNAL":
            return f"{color}{style} [WrenchCL]{active_preset.RESET}"
        elif level == "DATA":
            return f"{color}{style}DATA    {active_preset.RESET}"
        else:
            return f"{color}{style}%(levelname)-8s{active_preset.RESET}"

    def _get_highlight_function(self):
        """Get the highlight function - this would be injected from markup processor."""
        # This would be provided by a MarkupProcessor service
        from .MarkupHandlers import highlight_literals
        return highlight_literals


class EnvPrefixGenerator:
    """Generates environment prefixes for log messages."""

    def __init__(self, color_service: ColorService):
        self.color_service = color_service

    def generate_prefix(
            self, env_metadata: Dict, config_state,
            dimmed_color: str, dimmed_style: str,
            color: str, style: str
            ) -> str:
        """Generate environment prefix for log messages."""

        if config_state.should_strip_ansi:
            dimmed_color = dimmed_style = color = style = ''

        prefix = []
        first_color_flag = False
        presets = self.color_service.get_current_presets()

        if env_metadata.get('project') and config_state.should_show_env_prefix:
            prefix.append(f"{color}{style}{env_metadata['project'].upper()}{presets.RESET}")
            first_color_flag = True

        if env_metadata.get('env') and config_state.should_show_env_prefix:
            color_to_use = dimmed_color if first_color_flag else color
            style_to_use = dimmed_style if first_color_flag else style
            prefix.append(f"{color_to_use}{style_to_use}{env_metadata['env'].upper()}{presets.RESET}")

        if env_metadata.get('project_version') and config_state.should_show_env_prefix:
            color_to_use = dimmed_color if first_color_flag else color
            style_to_use = dimmed_style if first_color_flag else style
            prefix.append(f"{color_to_use}{style_to_use}{env_metadata['project_version']}{presets.RESET}")

        if env_metadata.get('run_id') and config_state.should_show_env_prefix:
            color_to_use = dimmed_color if first_color_flag else color
            style_to_use = dimmed_style if first_color_flag else style
            prefix.append(f"{color_to_use}{style_to_use}{env_metadata['run_id'].upper()}{presets.RESET}")

        if prefix:
            return f' {color}{style}:{presets.RESET} '.join(prefix) + f" {color}{style}|{presets.RESET} "
        return ''
