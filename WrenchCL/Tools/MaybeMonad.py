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

import builtins

class Maybe:
    """
    A utility class that provides a way to chain method calls and operations on an object that may be None.
    Supports context manager usage and built-in function delegation.

    Attributes:
        value: The value to be wrapped by Maybe
        _chain: A flag indicating whether chaining is enabled.
    """

    def __init__(self, value):
        """
        Initializes the Maybe instance with the given value.

        :param value: The value to wrap.
        """
        self.value = value
        self._chain = False  # Control flag for chaining behavior

    def __enter__(self):
        """
        Enables chaining when entering a context.

        :returns: The Maybe instance with chaining enabled.
        """
        self._chain = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Disables chaining when exiting a context.
        """
        self._chain = False

    def _forward_chain(self, value, force_chain=False):
        """
        Forwards the value within a new Maybe instance if chaining is enabled.

        :param value: The value to forward.
        :param force_chain: Whether to force chaining regardless of the current chain state.
        :returns: A Maybe instance or the raw value based on chaining state.
        """
        may_inst = Maybe(value)
        may_inst._chain = True if force_chain or self._chain else False
        return may_inst if may_inst._chain else value

    def __getattr__(self, name):
        """
        Handles attribute access and method calls on the wrapped value. Supports built-in functions.

        :param name: The attribute or method name.
        :returns: A callable or the attribute value, wrapped in a Maybe instance if chaining.
        """
        if Maybe._is_builtin_function(name):
            def wrapped_builtin_function(*args, **kwargs):
                if self.value is None:
                    return self._forward_chain(None, True)
                try:
                    func = getattr(builtins, name)
                    result = func(*args, self.value, **kwargs)
                    if isinstance(result, (map, filter)):
                        result = list(result)
                    return self._forward_chain(result, True)
                except Exception:
                    return self._forward_chain(None, True)

            return wrapped_builtin_function
        else:
            def method(*args, **kwargs):
                if self.value is None:
                    return self._forward_chain(None, True)
                try:
                    attr = getattr(self.value, name, None)
                    result = attr(*args, **kwargs) if callable(attr) else attr
                    return self._forward_chain(result, True)
                except Exception:
                    return self._forward_chain(None, True)

            return method

    @staticmethod
    def _is_builtin_function(func_name):
        """
        Checks if a name corresponds to a built-in function.

        :param func_name: The name to check.
        :returns: True if the name is a built-in function, False otherwise.
        """
        return callable(getattr(builtins, func_name, None))

    def end_maybe(self):
        """
        Disables chaining and returns the raw value.

        :returns: The raw value wrapped by the Maybe instance.
        """
        self._chain = False
        return self.value

    def __repr__(self):
        """
        Returns the string representation of the Maybe instance.

        :returns: The string representation of the wrapped value.
        """
        return f"Maybe({repr(self.value)})" if self._chain else repr(self.value)

    # Aliases for end_maybe method
    get_value = end_maybe
    resolve = end_maybe
    extract = end_maybe
    result = end_maybe
    done = end_maybe
    value = end_maybe
    exit = end_maybe
    out = end_maybe
    chain_break = end_maybe
