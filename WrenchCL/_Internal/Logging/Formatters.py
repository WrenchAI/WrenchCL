#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
import contextvars
import json
import logging
from contextvars import Context
from typing import Optional, Callable, Dict

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
    def __init__(self, env_metadata: dict, forced_color: bool, highlight_func: Callable, traced: bool = False, deployed: bool = False):
        super().__init__()
        self.env_metadata = env_metadata
        self.color_mode = forced_color
        self.highlight_func = highlight_func
        self.traced = traced
        self.deployed = deployed

    @staticmethod
    def _extract_generic_context() -> dict:
        """
        Extract known context values (user_id, organization_id, service_name) from:
        - os.environ
        - contextvars
        - deeply nested dicts or object trees (with cycle protection & depth limit)
        """
        context_data: dict = {}

        user_keys = {
                "user_id", "usr_id", "entity_id", "user_entity_id", "subject_id",
                "client_id", "user_name", "username",
                }
        org_keys = {
                "client_id", "org_id", "organization_id", "tenant_id",
                "team_id", "workspace_id", "project_id",
                }
        service_keys = {
                "service_id", "service_name", "application", "app_name", "dd_service",
                "aws_function_name", "aws_service", "lambda_name", "lambda_function",
                "aws_function", "project_name", "project",
                }

        # Prevent infinite recursion on cyclic structures; keep traversal shallow.
        MAX_DEPTH = 4
        seen: set[int] = set()

        def check_keys(key: str, value: object, depth: int) -> dict:
            result: dict = {}
            if not isinstance(key, str):
                try:
                    key = str(key)
                except Exception:
                    key = ""
            k = key.lower()

            if k in user_keys:
                result["user_id"] = value
            elif k in org_keys:
                result["organization_id"] = value
            elif k in service_keys:
                result["service_name"] = value

            if depth >= MAX_DEPTH:
                return result

            try:
                if isinstance(value, dict):
                    oid = id(value)
                    if oid in seen:
                        return result
                    seen.add(oid)
                    result.update(scan_dict(value, depth + 1))
                elif hasattr(value, "__dict__"):
                    oid = id(value)
                    if oid in seen:
                        return result
                    seen.add(oid)
                    try:
                        result.update(scan_dict(vars(value), depth + 1))
                    except Exception:
                        pass
            except Exception:
                pass

            return result

        def scan_dict(data: dict, depth: int) -> dict:
            found: dict = {}
            try:
                items = data.items()
            except Exception:
                return found
            for k, v in items:
                found.update(check_keys(k, v, depth))
            return found

        def scan_ctx(ctx: "Context") -> dict:
            found: dict = {}
            try:
                for var in ctx:
                    try:
                        value = ctx.get(var)
                    except Exception:
                        continue
                    found.update(check_keys(var.name, value, depth=0))
            except Exception:
                pass
            return found

        context_data.update(scan_ctx(contextvars.copy_context()))
        return context_data

    def format(self, record: logging.LogRecord) -> str:
        ctx = {}
        dd = {
                "dd.env": self.env_metadata.get("env"),
                "dd.service": self.env_metadata.get("project") or ctx.get('service_name'),
                "dd.version": self.env_metadata.get("project_version")
                }
        ctx.update(self._extract_generic_context())

        if self.traced:
            dd.update({
                    "dd.trace_id": str(getattr(record, "dd.trace_id", 0)),
                    "dd.span_id": str(getattr(record, "dd.span_id", 0))})

        log_record = {
                "level": record.levelname,
                "message": record.getMessage(),
                "source": {
                        "module": record.module,
                        "function": record.funcName,
                        "line": record.lineno,
                        },
                "log_info": {
                        "logger": record.name,
                        "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
                        }
                }

        if dd:
            log_record['trace'] = dd
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        if len(ctx) > 0:
            log_record['context'] = ctx

        if self.deployed:
            dumped_json = json.dumps(log_record, default=str, ensure_ascii=False)
        else:
            dumped_json = json.dumps(log_record, default=str, ensure_ascii=False, indent=2)

        if self.color_mode is True and not self.deployed:
            dumped_json = self.highlight_func(dumped_json)

        return dumped_json


class FileLogFormatter(logging.Formatter):
    def __init__(self, base_formatter: logging.Formatter):
        super().__init__(base_formatter._fmt, base_formatter.datefmt)
        self._base_formatter = base_formatter

    def format(self, record: logging.LogRecord) -> str:
        raw = self._base_formatter.format(record)
        from _Internal.Logging.logging_utils import remove_ansi
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
