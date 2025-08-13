#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

import os
import threading
from dataclasses import replace, dataclass
from typing import Optional, Literal, Dict, Any

from .DataClasses import LogLevel, logLevels


@dataclass(frozen=True)  # Immutable config state
class LoggerConfigState:
    """Immutable configuration state - no mutations allowed."""
    mode: str = 'terminal'              # 'terminal', 'json', or 'compact'
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
        return self.mode == 'terminal'

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


class ConfigManager:
    """
    Manages logger configuration with immutable state and clear change tracking.

    This class provides a clean API for configuration management while ensuring
    that all config changes are tracked and applied atomically.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._state = LoggerConfigState()
        self._env_detector = EnvironmentDetector()
        self._change_listeners = []

        # Apply initial environment detection
        self._apply_environment_config()

    @property
    def current_state(self) -> LoggerConfigState:
        """Get current immutable config state."""
        with self._lock:
            return self._state

    def add_change_listener(self, callback):
        """Add a callback that gets called when config changes."""
        with self._lock:
            self._change_listeners.append(callback)

    def configure(self,
                  mode: Optional[Literal['terminal', 'json', 'compact']] = None,
                  level: Optional[logLevels] = None,
                  color_enabled: Optional[bool] = None,
                  highlight_syntax: Optional[bool] = None,
                  verbose: Optional[bool] = None,
                  trace_enabled: Optional[bool] = None,
                  deployment_mode: Optional[bool] = None,
                  force_markup: Optional[bool] = None) -> LoggerConfigState:
        """
        Create new config state with specified changes.
        Returns the new state and notifies listeners.
        """

        with self._lock:
            changes = {}

            if mode is not None:
                changes['mode'] = mode
                # JSON mode implies deployment
                if mode == 'json' and deployment_mode is None:
                    changes['deployed'] = True

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

            # Create new immutable state
            old_state = self._state
            new_state = self.new_config(**changes)
            self._state = new_state

            # Notify listeners of the change
            self._notify_change_listeners(old_state, new_state)

            return new_state

    def reinitialize(self) -> LoggerConfigState:
        """Reapply environment detection and return new state."""
        with self._lock:
            old_state = self._state
            self._apply_environment_config()
            self._notify_change_listeners(old_state, self._state)
            return self._state

    def create_temporary_state(self, **overrides) -> LoggerConfigState:
        """Create a temporary state with overrides (for context managers)."""
        with self._lock:
            return self.new_config(**overrides)

    def apply_temporary_state(self, temp_state: LoggerConfigState) -> LoggerConfigState:
        """Apply a temporary state and return the old state."""
        with self._lock:
            old_state = self._state
            self._state = temp_state
            self._notify_change_listeners(old_state, temp_state)
            return old_state

    def restore_state(self, previous_state: LoggerConfigState):
        """Restore a previous state."""
        with self._lock:
            old_state = self._state
            self._state = previous_state
            self._notify_change_listeners(old_state, previous_state)

    def get_env_metadata(self) -> Dict[str, Optional[str]]:
        """Get current environment metadata."""
        return self._env_detector.get_env_metadata()

    def _apply_environment_config(self):
        """Apply environment-based configuration."""
        env_overrides = self._env_detector.detect_deployment()
        if env_overrides:
            self._state = self.new_config(**env_overrides)

    def _notify_change_listeners(self, old_state: LoggerConfigState, new_state: LoggerConfigState):
        """Notify all registered listeners about config changes."""
        for callback in self._change_listeners:
            try:
                callback(old_state, new_state)
            except Exception:
                # Don't let listener errors break the config system
                pass

    @staticmethod
    def should_update_formatters(old_config, new_config) -> bool:
        """Helper to determine if formatters need updating."""
        return (old_config.mode != new_config.mode or
                old_config.color_enabled != new_config.color_enabled or
                old_config.deployed != new_config.deployed)

    # noinspection PyTypeChecker
    def new_config(self, **settings: dict[str, Any]):
        if settings.get('level') is not None:
            settings['level'] = LogLevel(settings['level'])
        return replace(self._state, **settings)