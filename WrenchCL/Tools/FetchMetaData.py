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

import mimetypes
import os
from datetime import datetime

import requests


def get_metadata(file_source, is_url=True):
    """
    Get metadata of a file from a URL or file path.

    :param file_source: URL or file path of the file
    :type file_source: str
    :param is_url: Flag indicating if the file_source is a URL, defaults to True
    :type is_url: bool, optional
    :return: Dictionary containing metadata
    :rtype: dict
    """
    metadata = {}

    if is_url:
        # Handle the URL case
        response = requests.head(file_source)
        response.raise_for_status()

        metadata['content_type'] = response.headers.get('Content-Type')
        metadata['content_length'] = response.headers.get('Content-Length')
        metadata['last_modified'] = response.headers.get('Last-Modified')
        metadata['url'] = file_source

        if metadata['last_modified']:
            metadata['last_modified'] = datetime.strptime(metadata['last_modified'], '%a, %d %b %Y %H:%M:%S %Z')
    else:
        # Handle the file path case
        metadata['file_path'] = file_source
        metadata['file_size'] = os.path.getsize(file_source)
        metadata['creation_time'] = datetime.fromtimestamp(os.path.getctime(file_source)).isoformat()

        mime_type, _ = mimetypes.guess_type(file_source)
        metadata['mime_type'] = mime_type

    return metadata

# Example usage:
# metadata = get_metadata("https://example.com/file.txt")
# metadata = get_metadata("/path/to/file.txt", is_url=False)
