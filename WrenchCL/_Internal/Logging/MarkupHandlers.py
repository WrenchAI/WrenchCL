#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
import re

from .ColorService import ColorPresets
from .DataClasses import LogLevel


def highlight_data(msg: str, preset: ColorPresets) -> str:
    c = preset

    # Python style dicts: support both 'key' and "key"
    msg = re.sub(
            r'(?P<key>[\'"][^\'"]+[\'"])(?P<colon>\s*:)',
            lambda m: f"{c.INFO}{m.group('key')}{c.RESET_FORE}{c.COLOR_COLON}{m.group('colon')}{c.RESET_FORE}",
            msg
            )

    msg = msg.replace('{', f"{c.COLOR_BRACE_OPEN}{{{c.RESET_FORE}")
    msg = msg.replace('}', f"{c.COLOR_BRACE_CLOSE}}}{c.RESET_FORE}")
    msg = msg.replace('(', f"{c.COLOR_PAREN_OPEN}({c.RESET_FORE}")
    msg = msg.replace(')', f"{c.COLOR_PAREN_CLOSE}){c.RESET_FORE}")
    msg = msg.replace(':', f"{c.COLOR_COLON}:{c.RESET_FORE}")
    msg = msg.replace(',', f"{c.COLOR_COMMA},{c.RESET_FORE}")

    msg = re.sub(r'(?<=\n)(\s*)\[', lambda m: f"{m.group(1)}{c.COLOR_BRACKET_OPEN}[{c.RESET_FORE}", msg)
    msg = re.sub(r'](?=\n)', lambda m: f"{c.COLOR_BRACKET_CLOSE}]{c.RESET_FORE}", msg)

    return msg


def highlight_literals_json(msg: str, preset: ColorPresets) -> str:
    c = preset

    # Highlight log levels
    level_keywords = {
            "DEBUG": c.DEBUG, "INFO": c.INFO, "WARNING": c.WARNING,
            "WARN": c.WARNING, "ERROR": c.ERROR, "CRITICAL": c.CRITICAL
            }
    for keyword, color in level_keywords.items():
        msg = re.sub(rf'\b{keyword}\b', f"{color}{keyword}{c.RESET_FORE}", msg, flags=re.IGNORECASE)

    # Highlight string keys with double quotes
    msg = re.sub(
            r'(?P<key>"[^"]+?")(?P<colon>\s*:)',
            lambda m: f"{c.COLOR_KEY}{m.group('key')}{c.RESET_FORE}{c.COLOR_COLON}{m.group('colon')}{c.RESET_FORE}",
            msg
            )

    # Highlight brackets/braces/commas
    msg = msg.replace('{', f"{c.COLOR_BRACE_OPEN}{{{c.RESET_FORE}")
    msg = msg.replace('}', f"{c.COLOR_BRACE_CLOSE}}}{c.RESET_FORE}")
    msg = msg.replace('(', f"{c.COLOR_PAREN_OPEN}({c.RESET_FORE}")
    msg = msg.replace(')', f"{c.COLOR_PAREN_CLOSE}){c.RESET_FORE}")
    msg = msg.replace(':', f"{c.COLOR_COLON}:{c.RESET_FORE}")
    msg = msg.replace(',', f"{c.COLOR_COMMA},{c.RESET_FORE}")

    msg = re.sub(r'(?<=\n)(\s*)\[', lambda m: f"{m.group(1)}{c.COLOR_BRACKET_OPEN}[{c.RESET_FORE}", msg)
    msg = re.sub(r'](?=\n)', lambda m: f"{c.COLOR_BRACKET_CLOSE}]{c.RESET_FORE}", msg)

    return msg


def highlight_literals(msg: str, preset: ColorPresets) -> str:
    from .logging_utils import remove_ansi
    msg = remove_ansi(msg)

    c = preset

    # Highlight numbers
    msg = re.sub(r'(?<![\w-])(\d+(?:\.\d+)?[a-zA-Z%]*)\b',
                 lambda m: f"{c.COLOR_NUMBER}{m.group(1)}{c.RESET_FORE}", msg)

    # Highlight UUIDs
    msg = re.sub(
            r'\b([0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})\b',
            lambda m: f"{c.COLOR_UUID}{m.group(1)}{c.RESET_FORE}",
            msg, flags=re.IGNORECASE)

    # Highlight placeholders like %s or %{name}s
    msg = re.sub(r'%\{?[a-zA-Z0-9_]*s}?\b',
                 lambda m: f"{c.COLOR_COLON}{m.group(0)}{c.RESET_FORE}", msg)

    # Highlight square brackets (at line start/end only)
    msg = re.sub(r'(?<=\n)(\s*)\[', lambda m: f"{m.group(1)}{c.COLOR_BRACKET_OPEN}[{c.RESET_FORE}", msg)
    msg = re.sub(r'](?=\n)', lambda m: f"{c.COLOR_BRACKET_CLOSE}]{c.RESET_FORE}", msg)

    # Highlight braces, parens, pipes
    msg = re.sub(r'(?<!\\)([{}|])', lambda m: f"{c.COLOR_COLON}{m.group(1)}{c.RESET_FORE}", msg)

    # Highlight literals: true, false, null, none, nan
    msg = re.sub(r'\b(true|false|null|none|nan)\b', lambda m: {
            "true": f"{c.COLOR_TRUE}{m.group(0)}{c.RESET_FORE}",
            "false": f"{c.COLOR_FALSE}{m.group(0)}{c.RESET_FORE}",
            "null": f"{c.COLOR_NONE}{m.group(0)}{c.RESET_FORE}",
            "none": f"{c.COLOR_NONE}{m.group(0)}{c.RESET_FORE}",
            "nan": f"{c.COLOR_NONE}{m.group(0)}{c.RESET_FORE}"
            }[m.group(0).lower()], msg, flags=re.IGNORECASE)

    return msg


# noinspection PyTypeChecker
def get_spacer(word: str, length: int, char: str = '─') -> str:
    if not char:
        char = '─'
    if len(word) >= length:
        return str(char * length)

    length = (length - len(word)) // 2
    return str(char * length + word + char * length)


# noinspection PyTypeChecker
def add_data_markers(msg: str, preset: ColorPresets, level: LogLevel, head=False) -> str:
    if len(msg.strip().splitlines()) <= 1:
        return msg

    is_data = level == "DATA"
    header = head and not is_data
    color = preset.get_color_by_level(level)
    style = preset.get_level_style(level)
    reset = preset.RESET

    indent_size = 4
    pad = ' ' * indent_size
    lines = msg.splitlines(keepends=True)
    from .logging_utils import remove_ansi
    content_width = max(len(remove_ansi(line.strip())) for line in lines)

    total_width = content_width + (indent_size * 2)

    arm_len = min(indent_size * 10, max(1, content_width // 2))
    bar_len = total_width - arm_len

    top_bar = ('─' * total_width)
    bot_bar = ('─' * total_width)
    right_corner = '┐'
    left_corner = '└'
    markup = f"{color}{style}"

    if is_data:
        top_bar = get_spacer("DATA", arm_len) + ' ' * bar_len
        bot_bar = ' ' * bar_len + get_spacer("END", arm_len)
        right_corner = ' '
        left_corner = ' '
    elif header:
        top_bar = get_spacer(level, total_width)

    top_border = f"{reset}{markup}{'┌'}{top_bar}{right_corner}"
    if is_data:
        top_border = f"{markup}{'┌'}{top_bar}{right_corner}{reset}"
    bottom_border = f"{markup}{left_corner}{bot_bar}{'┘'}{reset}"

    content = ''.join(f"{pad}{line}" for line in lines)
    if not content.endswith('\n'):
        content += '\n'
    if not content.startswith('\n'):
        content = '\n' + content

    return top_border + content + bottom_border
