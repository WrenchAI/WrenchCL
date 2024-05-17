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

def SingletonClass(cls):
    """
    Decorator for a class to implement the Singleton pattern. This decorator ensures that only one instance of the
    decorated class can exist at any time. If an instance of the class already exists, it returns that instance;
    otherwise, it creates and returns a new instance.

    The Singleton pattern is particularly useful when exactly one object is needed to coordinate actions across the
    system, such as in the case of managing database connections.

    :param cls: The class to be decorated as a Singleton.
    :type cls: type
    :returns: A wrapper function that manages the instantiation of the singleton class, ensuring that only one
              instance exists.
    :rtype: function

    **Example**::

        >>> @SingletonClass
        ... class DatabaseManager:
        ...     def __init__(self, connection_string):
        ...         self.connection_string = connection_string
        ...
        >>> db_manager1 = DatabaseManager('db_connection_string')
        >>> db_manager2 = DatabaseManager('db_connection_string')
        >>> assert db_manager1 is db_manager2  # Both variables point to the same instance
    """
    instances = {}

    def get_instance(*args, **kwargs):
        """
        Returns the singleton instance of the class, creating it if it does not already exist.

        :param args: Positional arguments for the class constructor.
        :param kwargs: Keyword arguments for the class constructor.
        :returns: The singleton instance of the class.
        """
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance
