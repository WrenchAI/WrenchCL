"""
StreamManager - Manages system streams and root logger
"""
#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

import sys
import warnings
from typing import Literal

from ..DataClasses import logLevels
from ..._custom_types import StdStreamMode


class StreamManager:
    """Manages system streams and root logger"""

    def __init__(self, parent_logger):
        self.parent = parent_logger

    def attach(self, level: logLevels, silence_others: bool = False, stream=sys.stdout) -> None:
        """Attach a WrenchCL-formatted stream handler to the root logger"""
        config = self.parent.state_manager.current_state
        env_metadata = self.parent.state_manager.get_env_metadata()

        self.parent.state_manager.global_logger_manager.attach_global_stream(
                level=level,
                silence_others=silence_others,
                stream=stream,
                config_state=config,
                env_metadata=env_metadata
                )
        self.parent._internal.log_internal(f"Attached global stream at level {level}")

    def intercept_exceptions(
            self, install_hooks: bool = True,
            std_stream_mode: Literal['none', 'stderr', 'both'] = "none"
            ) -> None:
        """Configure global exception interception and stdout/stderr suppression"""
        if std_stream_mode is None:
            std_stream_mode = "none"
        mode = StdStreamMode(std_stream_mode)
        self.parent.state_manager.global_logger_manager.configure_interception(
                install_hooks=install_hooks,
                std_stream_mode=mode,
                )
        self.parent._internal.log_internal(f"Configured exception interception: hooks={install_hooks}, streams={std_stream_mode}")

    def suppress(self, mode: str = "both") -> None:
        """Apply or change stdout/stderr suppression without altering hooks"""
        self.parent.state_manager.global_logger_manager.suppress_std_streams(StdStreamMode(mode))
        self.parent._internal.log_internal(f"Suppressed std streams: {mode}")

    def force_markup(self) -> None:
        """Force enable colorful console output with ANSI escape codes"""
        try:
            import colorama
            colorama.deinit()
            colorama.init(strip=False, convert=False)
            sys.stdout = colorama.AnsiToWin32(sys.stdout).stream
            sys.stderr = colorama.AnsiToWin32(sys.stderr).stream

            self.parent.state_manager.configure(force_markup=True, color_enabled=True)

            config = self.parent.state_manager.current_state
            if config.force_markup and config.deployed:
                warnings.warn("Forcing Markup in deployment mode is not recommended...",
                              category=RuntimeWarning, stacklevel=5)

            self.parent._internal.log_internal("Forced color output enabled.")
        except ImportError:
            self.parent._internal.log_internal("Colorama not installed. Forcing markup is not possible.")

    def redirect_stdout(self) -> None:
        """Redirect stdout through WrenchCL formatting"""
        # This would need implementation based on your internal stream management
        self.parent._internal.log_internal("Redirecting stdout")

    def redirect_stderr(self) -> None:
        """Redirect stderr through WrenchCL formatting"""
        # This would need implementation based on your internal stream management  
        self.parent._internal.log_internal("Redirecting stderr")

    def restore_stdout(self) -> None:
        """Restore original stdout"""
        # This would need implementation based on your internal stream management
        self.parent._internal.log_internal("Restoring stdout")

    def restore_stderr(self) -> None:
        """Restore original stderr"""
        # This would need implementation based on your internal stream management
        self.parent._internal.log_internal("Restoring stderr")
