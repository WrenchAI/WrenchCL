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
import requests
from io import BytesIO


def image_to_base64(image_source, is_url=True):
    """
    Convert an image from a URL or file path to a Base64 string.

    :param image_source: URL or file path of the image
    :type image_source: str
    :param is_url: Flag indicating if the image_source is a URL, defaults to True
    :type is_url: bool, optional
    :return: Base64 encoded string of the image
    :rtype: str
    """
    if is_url:
        # Handle the URL case
        response = requests.get(image_source)
        response.raise_for_status()
        image_data = BytesIO(response.content)
    else:
        # Handle the file path case
        with open(image_source, "rb") as image_file:
            image_data = BytesIO(image_file.read())

    # Encode the image data to Base64
    base64_string = base64.b64encode(image_data.getvalue()).decode('utf-8')

    return base64_string

# Example usage:
# base64_str = image_to_base64("https://example.com/image.jpg")
# base64_str = image_to_base64("/path/to/image.jpg", is_url=False)
