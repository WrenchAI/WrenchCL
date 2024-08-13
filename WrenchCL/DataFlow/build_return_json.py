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


import json


# Created by Jeong Kim
# Github: https://github.com/dalmad2
# Annotated by Willem van der Schans
# Github: https://github.com/Kydoimos97


def build_return_json(code, response_body):
    """
    Constructs a JSON response body with the provided status code and message, optionally including a return dictionary.

    Args:
        code (int): The HTTP status code to be included in the response.
        response_body (any): A dictionary containing data to be included in the response body. Defaults to None.

    Returns:
        dict: A dictionary representing the JSON response containing the status code, message, and optionally the return dictionary.

    Raises:
        None: No explicit exceptions are raised within this function.
    """

    return {
        'statusCode': code,
        'body': json.dumps(response_body),
        'headers': {
            'Content-Type': 'application/json; charset=utf-8',
            'strict-transport-security': 'max-age=63072000; includeSubdomains; preload',
            'content-security-policy': "default-src 'none'; img-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'",
            'x-content-type-options': 'nosniff',
            'x-frame-options': 'DENY',
            'x-xss-protection': '1; mode=block'
        }
    }
