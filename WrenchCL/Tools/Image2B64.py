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
import hashlib
from io import BytesIO

import requests


def get_hash(data):
    """
    Generate SHA-1 hash for the given data.

    :param data: Data in bytes
    :return: SHA-1 hash of the data
    :rtype: str
    """
    if isinstance(data, str):
        data = data.encode('utf-8')


    sha1 = hashlib.sha1()
    sha1.update(data)
    return sha1.hexdigest()


def image_to_base64(image_source, is_url=True, return_hash=False):
    """
    Convert an image from a URL or file path to a Base64 string, optionally returning its SHA-1 hash.

    :param image_source: URL or file path of the image
    :type image_source: str
    :param is_url: Flag indicating if the image_source is a URL, defaults to True
    :type is_url: bool, optional
    :param return_hash: Flag indicating if the SHA-1 hash of the image should be returned, defaults to False
    :type return_hash: bool, optional
    :return: Base64 encoded string of the image and optionally the SHA-1 hash in order
    :rtype: str | tuple(str, str)
    """
    if is_url:
        # Handle the URL case
        response = requests.get(image_source)
        response.raise_for_status()
        image_data = BytesIO(response.content).getvalue()
    else:
        # Handle the file path case
        with open(image_source, "rb") as image_file:
            image_data = BytesIO(image_file.read()).getvalue()

    # Encode the image data to Base64
    base64_string = base64.b64encode(image_data).decode('utf-8')

    if return_hash:
        image_hash = get_hash(image_data)
        return base64_string, image_hash

    return base64_string


def validate_base64(b64_string):
    """
    Validate a Base64 encoded string.

    :param b64_string: Base64 encoded string
    :type b64_string: str
    :return: True if the string is a valid Base64 encoded string, False otherwise
    :rtype: bool
    """
    try:
        # Decode the base64 string
        base64.b64decode(b64_string, validate=True)
        return True
    except (base64.binascii.Error, ValueError):
        return False
