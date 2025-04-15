

#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

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
