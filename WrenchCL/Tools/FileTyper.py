
#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
import base64
import mimetypes
from io import BytesIO
from pathlib import Path
from typing import Union, Tuple

import requests
from filetype import filetype

from .Image2B64 import validate_base64

try:
    from botocore.response import StreamingBody
    imports = True
except ImportError:
    imports = False


class UnsupportedFileTypeError(Exception):
    pass

def get_file_type(file_source: Union[str, Path, bytes, BytesIO, "StreamingBody"], is_url: bool = True) -> Tuple[str, str]:
    """
    Determine the file type of a file from a URL, file path, Base64 string, bytes, or BytesIO.

    :param file_source: URL, file path, Base64 string, bytes, or BytesIO of the file
    :type file_source: Union[str, Path, bytes, BytesIO, StreamingBody]
    :param is_url: Flag indicating if the file_source is a URL, defaults to True
    :type is_url: bool, optional
    :return: File type based on extension or MIME type
    :rtype: Tuple[str, str]
    :raises UnsupportedFileTypeError: If the file type cannot be determined.
    """

    if isinstance(file_source, (str, Path)):
        if validate_base64(file_source):
            base64_data = base64.b64decode(file_source)
        else:
            mime_type, _ = mimetypes.guess_type(str(file_source))
            if mime_type:
                return mimetypes.guess_extension(mime_type) or '', mime_type
            else:
                if is_url:
                    response = requests.get(str(file_source))
                    response.raise_for_status()
                    base64_data = response.content
                else:
                    with open(file_source, 'rb') as f:
                        base64_data = f.read()

    elif isinstance(file_source, bytes):
        if validate_base64(file_source.decode('utf-8')):
            base64_data = base64.b64decode(file_source)
        else:
            base64_data = file_source

    elif isinstance(file_source, BytesIO):
        base64_data = file_source.read()
        file_source.seek(0)

    elif imports and isinstance(file_source, StreamingBody):
        base64_data = file_source.read()

    else:
        raise ValueError("Unsupported file_source type.")

    if base64_data:
        kind = filetype.guess(base64_data)
        if kind:
            return kind.extension, kind.mime

    raise UnsupportedFileTypeError("Could not determine the file type.")

# Example usage:
# file_type = get_file_type("https://example.com/file.txt")
# file_type = get_file_type("/path/to/file.txt", is_url=False)
# file_type = get_file_type(base64_string)
# file_type = get_file_type(byte_data, is_url=False)
# file_type = get_file_type(BytesIO(byte_data), is_url=False)
# file_type = get_file_type(streaming_body, is_url=False)

