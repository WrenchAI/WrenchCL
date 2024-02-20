import pytest
from WrenchCL.Utility import Maybe

def test_oneline_methods():
    # Test chaining multiple methods in a single line
    maybe_chained = Maybe("Some String").lower().upper()
    # Assert that the chain doesn't break and results in the expected value
    assert maybe_chained.chain_break() == 'SOME STRING', "Chaining lower() then upper() should return uppercase string"

def test_raise_error_on_none():
    # Test that attempting to call a method on None raises an AttributeError
    temp_no_chain = Maybe(None).lower().resolve()
    # Assert that AttributeError is raised when calling upper() on a None value
    with pytest.raises(AttributeError):
        temp_no_chain.upper()

def test_return_raw_value_without_chaining():
    # Test getting the raw value without chaining further methods
    assert Maybe("Some String").lower().done() == 'some string', "Calling lower() should return lowercase string"

def test_handle_None():
    # Test that handling None returns None instead of raising an error
    assert Maybe(None).lower().result() is None, "Handling None with result() should return None"

def test_handle_None_methods():
    # Test chaining methods after handling None still returns None
    assert Maybe(None).lower().upper().done() is None, "Chaining methods after handling None should return None"

def test_context_manager_chaining():
    # Test dynamic method chaining within a context manager
    with Maybe("Dynamic Chaining") as maybe_dynamic:
        # Perform a series of method chains inside the context manager
        maybe_dynamic = maybe_dynamic.upper().lower().replace(' ', '')
        # Assert that the final result is as expected
        assert str(maybe_dynamic) == "Maybe('dynamicchaining')", "Chaining upper(), lower(), and replace() should match the expected string"
    # Assert that the value can be extracted correctly after exiting the context
    assert maybe_dynamic.exit() == 'dynamicchaining', "Exiting the context manager should yield the processed value"

def test_context_manager_None_chaining():
    # Test chaining methods on None within a context manager
    with Maybe(None) as maybe_dynamic:
        # Chain methods that do not modify the None value
        maybe_dynamic = maybe_dynamic.upper().lower().replace(' ', '')
        # Assert that the Maybe object still contains None
        assert str(maybe_dynamic) == "Maybe(None)", "Chaining methods on None should leave the Maybe object unchanged"
    # Assert that extracting the value after the context yields None
    assert maybe_dynamic.exit() is None, "Exiting the context manager with None should yield None"

def test_context_manager_None_no_allocation():
    # Test that no allocation or change occurs when chaining methods on None within a context manager
    with Maybe(None) as maybe_dynamic:
        # Chain methods without affecting the None value
        maybe_dynamic.upper().lower().replace(' ', '')
        # Assert that the Maybe object remains unchanged
        assert str(maybe_dynamic) == "Maybe(None)", "The Maybe object should remain as None when chaining methods on it"
    # Assert that the final outcome is None after exiting the context
    assert maybe_dynamic.out() is None, "The result should be None after chaining methods on None and exiting context"

def test_maybe_chain_with_filter():
    # Test chaining filter operations on a Maybe object containing a list
    result = Maybe([1, 2, 3, None, 4]).filter(lambda x: x is not None).filter(lambda x: x != 1).out()
    # Assert that the filter method removes None values from the list and can be chained
    assert result == [2, 3, 4], "Filtering should remove None and 1 values from the list"

def test_maybe_chain_with_none():
    # Test the behavior of chaining a filter method on a Maybe object that contains None
    result = Maybe(None).filter(lambda x: x is not None).done()
    # Assert that the result is None when starting with a None value
    assert result is None, "Chaining filter on None should return None"

def test_logical_eval():
    # Test logical evaluations within the Maybe monad
    result = Maybe(None).lower().done() == 'true'
    result2 = Maybe('True').lower().done() == 'true'
    # Assert that the logical evaluation of a None value is False
    assert not result, "The logical evaluation of a None value should be False"
    # Assert that the logical evaluation of a 'True' value is True after lowering it
    assert result2, "The logical evaluation should be True when 'True' is lowered and compared to 'true'"
