#  Copyright (c) $YEAR$. Copyright (c) $YEAR$ Wrench.AI., Willem van der Schans, Jeong Kim
#
#  MIT License
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#  All works within the Software are owned by their respective creators and are distributed by Wrench.AI.
#
#  For inquiries, please contact Willem van der Schans through the official Wrench.AI channels or directly via GitHub at [Kydoimos97](https://github.com/Kydoimos97).
#
import base64
from io import BytesIO
from pathlib import Path
from typing import Union, Optional, Tuple
import filetype
import requests
from botocore.response import StreamingBody
from .Image2B64 import validate_base64


import base64
from io import BytesIO
from pathlib import Path
from typing import Union, Optional, Tuple
import mimetypes
import filetype
import requests
from botocore.response import StreamingBody

class UnsupportedFileTypeError(Exception):
    pass

def get_file_type(file_source: Union[str, Path, bytes, BytesIO, StreamingBody], is_url: bool = True) -> Tuple[str, str]:
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
    base64_data: Optional[bytes] = None

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

    elif isinstance(file_source, StreamingBody):
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

