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
import requests
try:
    import magic
except ImportError as e:
    raise ImportError(
        "Failed to import 'magic'. Please install the appropriate library. "
        "On Windows, you can install it with:\n\n"
        "pip uninstall python-magic -y\n"
        "pip install WrenchCL[libmagic]\n\n"
        "On other platforms, ensure 'libmagic' is installed."
    ) from e


def get_file_type(file_source, is_url=True):
    """
    Determine the file type of a file from a URL or file path.

    :param file_source: URL or file path of the file
    :type file_source: str
    :param is_url: Flag indicating if the file_source is a URL, defaults to True
    :type is_url: bool, optional
    :return: File type based on extension or MIME type
    :rtype: str
    """
    if is_url:
        response = requests.head(file_source)
        response.raise_for_status()
        mime_type = response.headers.get('Content-Type')
    else:
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(file_source)

    file_extension = mimetypes.guess_extension(mime_type)

    return file_extension, mime_type

# Example usage:
# file_type = determine_file_type("https://example.com/file.txt")
# file_type = determine_file_type("/path/to/file.txt", is_url=False)
