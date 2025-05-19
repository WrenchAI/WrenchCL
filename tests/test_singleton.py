import pytest
from WrenchCL.Decorators import SingletonClass

from WrenchCL.Exceptions._internal import _SingletonViolationException


def test_singleton_violation_on_new():
    with pytest.raises(_SingletonViolationException) as exc_info:
        @SingletonClass
        class ViolatingSingleton:
            def __new__(cls):
                return super().__new__(cls)

    assert "Classes decorated with @SingletonClass must not override the '__new__' method." in str(exc_info.value)


def test_singleton_instance_identity():
    @SingletonClass
    class SingletonExample:
        def __init__(self):
            self.value = 42

    a = SingletonExample()
    b = SingletonExample()
    assert a is b
    assert a.value == 42


def test_singleton_init_called_once():
    counter = {"calls": 0}

    @SingletonClass
    class InitCounter:
        def __init__(self):
            counter["calls"] += 1

    _ = InitCounter()
    _ = InitCounter()
    assert counter["calls"] == 1


def test_singleton_allows_init_only():
    @SingletonClass
    class InitOnly:
        def __init__(self):
            self.data = "ok"

    inst = InitOnly()
    assert inst.data == "ok"