#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
from typing import Optional

from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from .LoggerConfigState import LoggerConfigState

from .DataClasses import LogLevel, logLevels
from .MarkupHandlers import highlight_literals, highlight_data, highlight_literals_json, add_data_markers
from .logging_utils import ensure_str, suggest_exception


class MarkupProcessor:
    """Handles all markup and highlighting logic."""

    def __init__(self, color_service):
        self.color_service = color_service

    def process_message_markup(self, msg: str, config_state: "LoggerConfigState", no_color: bool = False) -> str:
        """Apply markup to message based on configuration."""
        if not config_state.should_markup(force_override=not no_color) or not config_state.highlight_syntax:
            return msg

        presets = self.color_service.get_current_presets()
        # Always apply literal highlighting if markup is enabled
        msg = highlight_literals(msg, presets)
        # Apply mode-specific highlighting
        if config_state.should_highlight_data:
            msg = highlight_data(msg, presets)
        elif config_state.should_highlight_json_literals:
            msg = highlight_literals_json(msg, presets)

        return msg


class MessageProcessor:
    """Processes log messages - formatting, headers, data markers, etc."""

    def __init__(self, color_service, markup_processor):
        self.color_service = color_service
        self.markup_processor = markup_processor

    def process_log_message(
            self, level: LogLevel, args: tuple, config_state,
            header: Optional[str] = None, no_color: bool = False
            ) -> tuple:
        """
        Process a log message with all formatting, markup, and special handling.
        Returns (processed_message, exc_info)
        """

        # Convert args to list and process them
        processed_args = [ensure_str(arg) for arg in args if arg is not None]

        # Extract exceptions from args
        exc_info = None
        for idx, arg in enumerate(processed_args):
            if isinstance(arg, (Exception, BaseException)):
                # noinspection PyTypeChecker
                exc_info = processed_args.pop(idx)
                break

        # Add exception suggestions if configured
        if config_state.should_suggest_exceptions:
            suggestion = suggest_exception(exc_info)
            if suggestion:
                processed_args.append(suggestion)

        # Join message
        msg = '\n'.join(str(arg) for arg in processed_args)
        # Apply markup
        if str(level) not in ['INTERNAL', 'DEBUG']:
            msg = self.markup_processor.process_message_markup(msg, config_state, no_color=no_color)

        # Add header if needed
        if header and config_state.should_markup(force_override=not no_color):
            header_str = self.create_header(
                    header, level=level,
                    compact=config_state.is_compact_header_mode
                    )
            msg = f"{header_str}\n{msg}"

        # Format message based on config
        if config_state.single_line_mode:
            lines = msg.splitlines()
            msg = ' '.join([line.strip() for line in lines if len(line.strip()) > 0])
            msg = msg.replace('\n', ' ').replace('\r', '').strip()
        elif exc_info or level == 'DATA':
            presets = self.color_service.get_current_presets()
            # noinspection PyTypeChecker
            msg = add_data_markers(msg, presets, level, True)

        # Final message formatting
        if len(msg.strip().splitlines()) > 1 and not msg.startswith('\n'):
            msg = '\n' + msg

        return msg, exc_info

    def create_header(
            self, text: str, level: logLevels = 'HEADER', size: int = None,
            compact: bool = False
            ) -> Optional[str]:
        """Create a formatted header."""
        if not level:
            level = 'HEADER'

        level = LogLevel(level)
        presets = self.color_service.get_current_presets()
        color = presets.get_color_by_level(level)
        text = text.replace('_', ' ').replace('-', ' ').strip().upper()
        char = "─"
        size = size or (40 if compact else 80)

        # Apply color formatting
        formatted_text = f"{presets.BRIGHT}{color} {text} {presets.RESET}" if color else text
        # noinspection PyTypeChecker
        formatted = f"{presets.RESET}{formatted_text.center(size, char)}"

        if not compact:
            formatted = f"\n{formatted}"

        return formatted
