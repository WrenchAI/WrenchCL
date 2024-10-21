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

class IncompleteInitializationError(Exception):
    def __init__(self, message = None):
        if not message:
            super().__init__("Class is not initialized, please call initialization function first!")
        else:
            super().__init__(message)


class InitializationError(Exception):
    def __init__(self, message = None):
        if not message:
            super().__init__("Class could not be initialized!")
        else:
            super().__init__(message)

class ArgumentTypeError(Exception):
    def __init__(self, message = None):
        if not message:
            super().__init__("Invalid Argument Type passed")
        else:
            super().__init__(message)

class ArgumentValueError(Exception):
    def __init__(self, message = None):
        if not message:
            super().__init__("Invalid Argument Value passed")
        else:
            super().__init__(message)


__all__ = ['InitializationError', 'IncompleteInitializationError', 'ArgumentTypeError', 'ArgumentValueError',]
