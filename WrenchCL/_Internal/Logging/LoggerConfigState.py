#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
import logging
import os
import sys
import threading
import time
from dataclasses import replace, dataclass
from typing import Optional, Literal, Dict, Any

from .ColorService import ColorService, MockColorama
from .DataClasses import LogLevel, logLevels
from .Formatters import FormatterFactory
from .LogManagers import HandlerManager, GlobalLoggerManager
from .MessageProcessors import MarkupProcessor, MessageProcessor
from .logging_utils import generate_run_id


@dataclass(frozen=True)  # Immutable config state
class LoggerConfigState:
    """Immutable configuration state - no mutations allowed."""
    mode: str = 'terminal'  # 'terminal', 'json', or 'compact'
    highlight_syntax: bool = True
    verbose: bool = False
    deployed: bool = False
    dd_trace_enabled: bool = False
    color_enabled: bool = True
    force_markup: bool = False
    level: LogLevel = LogLevel('INFO')

    # Derived properties - computed from base config
    def should_markup(self, force_override: bool = False) -> bool:
        """Determines if markup/highlighting should be applied."""
        if force_override:
            return True

        # Basic requirements for markup
        if not self.color_enabled or not self.highlight_syntax:
            return False

        # Deployment check
        if self.deployed:
            return False

        # Force markup handling
        if self.force_markup and self.mode == 'json':
            return False

        return True

    def should_markup_with_override(self, force: bool = False) -> bool:
        """Determines markup with potential force override."""
        if force:
            return True
        return self.should_markup

    @property
    def single_line_mode(self) -> bool:
        """Determines if logs should be formatted as single lines."""
        return self.mode == 'compact' or self.deployed

    @property
    def should_use_json_formatter(self) -> bool:
        """Determines if JSON formatter should be used."""
        return self.mode == 'json'

    @property
    def should_show_env_prefix(self) -> bool:
        """Determines if environment prefix should be shown."""
        return self.deployed or self.verbose

    @property
    def should_strip_ansi(self) -> bool:
        """Determines if ANSI codes should be stripped."""
        return not self.color_enabled or self.deployed

    @property
    def should_suggest_exceptions(self) -> bool:
        """Determines if exception suggestions should be provided."""
        # return self.mode == 'terminal'
        return True

    @property
    def should_highlight_json_literals(self) -> bool:
        """Determines if JSON literals should be highlighted."""
        return (self.mode == 'json'
                and not self.deployed
                and self.should_markup)

    @property
    def should_highlight_data(self) -> bool:
        """Determines if data highlighting should be applied."""
        return (self.mode != 'json'
                and self.should_markup)

    @property
    def should_add_data_markers(self) -> bool:
        """Determines if data markers should be added."""
        return True  # This seems to always be true in the original logic

    @property
    def should_enable_dd_trace_logging(self) -> bool:
        """Determines if Datadog trace logging should be enabled."""
        return self.dd_trace_enabled and self.mode == 'json'

    @property
    def is_compact_header_mode(self) -> bool:
        """Determines if headers should use compact formatting."""
        return self.mode == 'compact'

    def should_format_message(self, no_format: bool = False) -> bool:
        """Determines if message formatting should be applied."""
        if self.deployed:
            return False
        else:
            return not no_format

    def should_use_color(self, no_color: bool = False) -> bool:
        """Determines if color should be used."""
        return self.color_enabled and not no_color and not self.deployed


class EnvironmentDetector:
    """Detects deployment environment and provides environment-based config."""

    @staticmethod
    def detect_deployment() -> Dict[str, Any]:
        """Detect deployment environment and return config overrides."""
        overrides = {}

        # AWS Lambda detection
        if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
            overrides.update({
                    'deployed': True,
                    'color_enabled': False,
                    'mode': 'json'
                    })

        # AWS general detection
        if os.environ.get("AWS_EXECUTION_ENV"):
            overrides.update({
                    'deployed': True,
                    'color_enabled': False,
                    'mode': 'json'
                    })

        # Environment variable overrides
        color_mode = os.environ.get("COLOR_MODE", "").lower()
        if color_mode:
            overrides['color_enabled'] = color_mode == "true"

        dd_trace = os.environ.get("LOG_DD_TRACE", "").lower()
        if dd_trace:
            overrides['dd_trace_enabled'] = dd_trace == "true"
            if dd_trace == "true":
                overrides['mode'] = 'json'

        return overrides

    @staticmethod
    def get_env_metadata() -> Dict[str, Optional[str]]:
        """Extract environment metadata from system environment variables."""
        return {
                "env": os.getenv("ENV") or os.getenv('DD_ENV') or os.getenv("AWS_EXECUTION_ENV"),
                "project": os.getenv("PROJECT_NAME") or os.getenv('COMPOSE_PROJECT_NAME') or os.getenv("AWS_LAMBDA_FUNCTION_NAME"),
                "project_version": os.getenv("PROJECT_VERSION") or os.getenv("LAMBDA_TASK_ROOT") or os.getenv('REPO_VERSION'),
                }


class LoggerStateManager:
    """
    Single Source of Truth for:
    1. Configuration state
    2. ALL state-dependent services
    3. State application logic
    """
    _lock = threading.RLock()
    __logger_instance: Optional[logging.Logger] = None

    # State
    _state = LoggerConfigState()
    _run_id = generate_run_id()
    __base_level = 'INFO'
    __start_time = None
    __initialized = False

    # Services
    _env_detector = EnvironmentDetector()
    color_service = ColorService()
    global_logger_manager: Optional[GlobalLoggerManager] = None

    def __init__(self):
        self._init_color_service()
        self._initialize_color_dependents()
        self._initialize_formatter_dependents()
        self._apply_environment_config()

    def set_global_logger_manager(self, internal_log_callback):
        """
        Called once during cLogger init to set up GlobalLoggerManager.
        Needs internal_log callback from cLogger since that's UI/logging, not state.
        """
        self.global_logger_manager = GlobalLoggerManager(
                formatter_factory=self.formatter_factory,
                handler_manager=self.handler_manager,
                internal_logger=internal_log_callback
                )

    def _initialize_color_dependents(self):
        self.markup_processor = MarkupProcessor(self.color_service)
        self.message_processor = MessageProcessor(self.color_service, self.markup_processor)
        self.formatter_factory = FormatterFactory(self.color_service)

    def _initialize_formatter_dependents(self):
        self.handler_manager = HandlerManager(self.logging_instance, self.formatter_factory)

    def _init_color_service(self):
        try:
            import colorama
            self.color_service.enable_colors()
        except ImportError:
            pass

    def setup(self) -> bool:
        with self._lock:
            if self.initialized:
                return False
            self.handler_manager.flush_all_handlers()
            self.logging_instance.setLevel(int(LogLevel(self.__base_level)))
            self.handler_manager.add_handler(logging.StreamHandler, self.current_state, stream=sys.stdout, force_replace=True)
            self.logging_instance.propagate = False
            self.__initialized = True
            return True

    @property
    def logging_instance(self) -> logging.Logger:
        with self._lock:
            if not self.__logger_instance:
                self.__logger_instance = logging.getLogger('WrenchCL')
            return self.__logger_instance

    @property
    def current_state(self) -> LoggerConfigState:
        with self._lock:
            return self._state

    @property
    def run_id(self) -> str:
        return self._run_id

    def set_new_run_id(self):
        with self._lock:
            self._run_id = generate_run_id()
        return self._run_id

    @property
    def initialized(self) -> bool:
        with self._lock:
            return self.__initialized

    @initialized.setter
    def initialized(self, value: bool):
        with self._lock:
            self.__initialized = value

    @property
    def global_stream_configured(self) -> bool:
        with self._lock:
            return self.global_logger_manager.is_global_stream_configured

    @property
    def start_time(self) -> Optional[float]:
        with self._lock:
            return self.__start_time

    def start_timer(self):
        with self._lock:
            self.__start_time = time.time()

    def reset_timer(self):
        with self._lock:
            self.__start_time = None

    def get_elapsed_time(self) -> Optional[float]:
        with self._lock:
            if self.__start_time is None:
                return None
            return time.time() - self.__start_time

    @property
    def base_level(self) -> LogLevel:
        with self._lock:
            return LogLevel(self.__base_level)

    def configure(
            self,
            mode: Optional[Literal['terminal', 'json', 'compact']] = None,
            level: Optional[logLevels] = None,
            color_enabled: Optional[bool] = None,
            highlight_syntax: Optional[bool] = None,
            verbose: Optional[bool] = None,
            trace_enabled: Optional[bool] = None,
            deployment_mode: Optional[bool] = None,
            force_markup: Optional[bool] = None,
            suppress_autoconfig: Optional[bool] = False
            ) -> LoggerConfigState:
        """
        Configure state and apply ALL side effects.
        No external callbacks needed - everything happens here.
        """
        with self._lock:
            changes = {}

            if mode is not None:
                changes['mode'] = mode
                if not suppress_autoconfig:
                    if mode == 'json' and deployment_mode is None:
                        changes['deployed'] = True
                    if mode == 'terminal':
                        if deployment_mode is True:
                            changes['deployed'] = True
                            changes['color_enabled'] = False
                            changes['highlight_syntax'] = False
                            changes['verbose'] = False
                            changes['dd_trace_enabled'] = False
                            changes['force_markup'] = False
                        else:
                            changes['color_enabled'] = True
                            changes['highlight_syntax'] = True
                            changes['verbose'] = False
                            changes['deployed'] = False
                            changes['dd_trace_enabled'] = False
                            changes['force_markup'] = False

            if level is not None:
                changes['level'] = LogLevel(level)
            if color_enabled is not None:
                changes['color_enabled'] = color_enabled
            if highlight_syntax is not None:
                changes['highlight_syntax'] = highlight_syntax
            if verbose is not None:
                changes['verbose'] = verbose
            if deployment_mode is not None:
                changes['deployed'] = deployment_mode
            if trace_enabled is not None:
                changes['dd_trace_enabled'] = trace_enabled
            if force_markup is not None:
                changes['force_markup'] = force_markup

            old_state = self._state
            new_state = replace(self._state, **changes)
            self._state = new_state

            # Apply all side effects internally
            self._apply_state_changes(old_state, new_state)

            return new_state

    def _apply_state_changes(self, old_state: LoggerConfigState, new_state: LoggerConfigState):
        """
        Apply ALL side effects when state changes.
        This is the ONLY place where state changes affect services.
        """

        # 1. Color service
        if (old_state.color_enabled != new_state.color_enabled) or (new_state.color_enabled and isinstance(self.color_service._color_class, MockColorama)):
            if new_state.color_enabled:
                self.color_service.enable_colors()
            else:
                self.color_service.disable_colors()
            self._initialize_color_dependents()
        # 2. Logger instance level
        if old_state.level != new_state.level:
            self.logging_instance.setLevel(int(new_state.level))
            # Also update all handler levels
            if self.handler_manager:
                self.handler_manager.update_handler_levels(new_state.level)

        # 3. Formatters (if mode/color/deployment changed)
        if self._should_update_formatters(old_state, new_state):
            env_metadata = self.get_env_metadata()
            if self.handler_manager:
                self.handler_manager.update_all_formatters(new_state, env_metadata)

            # Also update global handlers if configured
        if self.global_logger_manager and self.global_logger_manager.is_global_stream_configured:
            self.global_logger_manager.update_global_handlers(new_state, self.get_env_metadata())

    def reinitialize(self) -> LoggerConfigState:
        """Reapply environment detection."""
        with self._lock:
            old_state = self._state
            self._apply_environment_config()
            self._apply_state_changes(old_state, self._state)
            return self._state

    def create_temporary_state(self, **overrides) -> LoggerConfigState:
        """Create temporary state without applying it."""
        with self._lock:
            if overrides.get('level') is not None and not isinstance(overrides['level'], LogLevel):
                overrides['level'] = LogLevel(overrides['level'])
            return replace(self._state, **overrides)

    def apply_temporary_state(self, temp_state: LoggerConfigState) -> LoggerConfigState:
        """Apply temporary state and return old state for restoration."""
        with self._lock:
            old_state = self._state
            self._state = temp_state
            self._apply_state_changes(old_state, temp_state)
            return old_state

    def restore_state(self, previous_state: LoggerConfigState) -> None:
        """Restore previous state from temporary context."""
        with self._lock:
            current_state = self._state
            self._state = previous_state
            self._apply_state_changes(current_state, previous_state)

    def get_env_metadata(self) -> Dict[str, Optional[str]]:
        return self._env_detector.get_env_metadata()

    def _apply_environment_config(self):
        """Apply environment-based configuration."""
        env_overrides = self._env_detector.detect_deployment()
        if env_overrides:
            if env_overrides.get('level') is not None and not isinstance(env_overrides['level'], LogLevel):
                env_overrides['level'] = LogLevel(env_overrides['level'])
            old_state = self._state
            self._state = replace(self._state, **env_overrides)
            self._apply_state_changes(old_state, self._state)

    @staticmethod
    def _should_update_formatters(old_config, new_config) -> bool:
        return (old_config.mode != new_config.mode or
                old_config.color_enabled != new_config.color_enabled or
                old_config.deployed != new_config.deployed)
