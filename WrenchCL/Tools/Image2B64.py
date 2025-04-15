
#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

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
