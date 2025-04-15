

#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

def coalesce(*args):
    """
    Returns the first non-None value in the given list of arguments. If all arguments are None, returns None.

    :param args: A variable number of arguments among which the first non-None value is to be found.
    :type args: any
    :return: The first argument that is not None, or None if all arguments are None.
    :rtype: any

    **Example**::

        >>> coalesce(None, None, "first non-none", 5)
        'first non-none'
        >>> coalesce(None, None, None)
        None

    **Note**:
        This function is analogous to the SQL COALESCE function and is useful for defaulting values when multiple potential inputs may contain None.
    """
    for arg in args:
        if arg is not None:
            return arg
    return None
