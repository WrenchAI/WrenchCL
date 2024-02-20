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
from typing import Any, Callable, Optional, Type


class Maybe:
    """A class that encapsulates a value to allow safe method chaining without raising exceptions on None values.

    The Maybe class is intended to be used in a way that it can chain method calls and attribute accesses
    even when some of them return None, without raising an AttributeError. When the context manager is used,
    it enables chaining by wrapping the result back into a Maybe object.
    """

    def __init__(self, value: Any):
        """Initialize the Maybe object with a value.

        Args:
            value (Any): The initial value to be encapsulated by the Maybe object.
        """
        self.value = value
        self._chain: bool = False  # Control flag for chaining behavior

    def __enter__(self) -> 'Maybe':
        """Enable chaining behavior as a context manager entry."""
        self._chain = True
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_val: Optional[Exception], exc_tb: Optional[Any]) -> None:
        """Disable chaining behavior on context manager exit."""
        self._chain = False

    def _forward_chain(self, value: Any, force_chain: bool = False) -> 'Maybe':
        """Internal method to forward the chain if chaining is enabled.

        Args:
            value (Any): The value to be forwarded.
            force_chain (bool): Force the chaining even if it's not enabled. Defaults to False.

        Returns:
            Maybe: A new Maybe object with the given value if chaining is enabled, otherwise the value itself.
        """
        may_inst = Maybe(value)
        may_inst._chain = self._chain or force_chain
        return may_inst if may_inst._chain else value

    def __getattr__(self, name: str) -> Callable:
        """Dynamically handle attribute access and method calls.

        If the attribute or method does not exist, or the value is None, it will continue the chain without raising.

        Args:
            name (str): The attribute or method name to access.

        Returns:
            Callable: A wrapped function that either performs the built-in function or method call or continues the chain.
        """
        if Maybe._is_builtin_function(name):
            def wrapped_builtin_function(*args, **kwargs) -> 'Maybe':
                # Method body here
                pass

            return wrapped_builtin_function
        else:
            def method(*args, **kwargs) -> 'Maybe':
                # Method body here
                pass

            return method

    @staticmethod
    def _is_builtin_function(func_name: str) -> bool:
        """Check if a name corresponds to a built-in function.

        Args:
            func_name (str): The name of the function to check.

        Returns:
            bool: True if the name corresponds to a built-in function, False otherwise.
        """
        return callable(getattr(builtins, func_name, None))

    def end_maybe(self) -> Any:
        """Force disable chaining and return the raw value.

        Returns:
            Any: The raw value without the Maybe encapsulation.
        """
        self._chain = False
        return self.value

    def __repr__(self) -> str:
        """Provide a string representation of the Maybe object.

        Returns:
            str: A string that represents the Maybe object, indicating whether it is chained or not.
        """
        return f"Maybe({repr(self.value)})" if self._chain else repr(self.value)

    # Alias methods for end_maybe with the same docstring
    get_value = resolve = extract = result = done = value = exit = out = chain_break = end_maybe
