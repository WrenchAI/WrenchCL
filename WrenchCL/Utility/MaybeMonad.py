import builtins


class Maybe:
    def __init__(self, value):
        self.value = value
        self._chain = False  # Control flag for chaining behavior

    def __enter__(self):
        # Context manager entry: enable chaining
        self._chain = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Context manager exit: disable chaining
        self._chain = False

    def _forward_chain(self, value, force_chain=False):
        may_inst = Maybe(value)
        may_inst._chain = True if force_chain or self._chain else False
        return may_inst if may_inst._chain else value

    def __getattr__(self, name):
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
        """Check if a name corresponds to a built-in function."""
        return callable(getattr(builtins, func_name, None))

    def end_maybe(self):
        # Force disable chaining and return the raw value
        self._chain = False
        return self.value

    def __repr__(self):
        # Representation based on whether value is wrapped or raw
        return f"Maybe({repr(self.value)})" if self._chain else repr(self.value)

    get_value = end_maybe
    resolve = end_maybe
    extract = end_maybe
    result = end_maybe
    done = end_maybe
    value = end_maybe
    exit = end_maybe
    out = end_maybe
    chain_break = end_maybe
