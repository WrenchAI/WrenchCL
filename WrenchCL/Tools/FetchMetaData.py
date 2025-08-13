

#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

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
