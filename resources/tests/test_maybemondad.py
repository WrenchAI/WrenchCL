import pytest
from WrenchCL.Utility import Maybe

def test_oneline_methods():
    maybe_chained = Maybe("Some String").lower().upper()
    assert maybe_chained.chain_break() == 'SOME STRING'

def test_raise_error_on_none():
    temp_no_chain = Maybe(None).lower().resolve()
    with pytest.raises(AttributeError):
        temp_no_chain.upper()

def test_return_raw_value_without_chaining():
    assert Maybe("Some String").lower().done() == 'some string'  # Using get_value

def test_handle_None():
    assert Maybe(None).lower().result() is None  # Using resolve

def test_handle_None_methods():
    assert Maybe(None).lower().upper().done() is None  # Using finalize

def test_context_manager_chaining():
    with Maybe("Dynamic Chaining") as maybe_dynamic:
        maybe_dynamic = maybe_dynamic.upper()  # Enable chaining dynamically
        maybe_dynamic = maybe_dynamic.lower()  # Continue chaining
        maybe_dynamic = maybe_dynamic.replace(' ', '')  # Keep chaining
        assert str(maybe_dynamic) == "Maybe('dynamicchaining')"
    assert maybe_dynamic.exit() == 'dynamicchaining'  # Using extract

def test_context_manager_None_chaining():
    with Maybe(None) as maybe_dynamic:
        maybe_dynamic = maybe_dynamic.upper()  # Enable chaining dynamically
        maybe_dynamic = maybe_dynamic.lower()  # Continue chaining
        maybe_dynamic = maybe_dynamic.replace(' ', '')  # Keep chaining
        assert str(maybe_dynamic) == "Maybe(None)"
    assert maybe_dynamic.exit() is None  # Using getValue

def test_context_manager_None_no_allocation():
    with Maybe(None) as maybe_dynamic:
        maybe_dynamic.upper().lower()  # Enable chaining dynamically
        maybe_dynamic.replace(' ', '')  # Keep chaining
        assert str(maybe_dynamic) == "Maybe(None)"
    assert maybe_dynamic.out() is None  # Using result

def test_maybe_chain_with_filter():
    result = Maybe([1, 2, 3, None, 4]).filter(lambda x: x is not None).filter(lambda x: x is not None).out()
    assert result == [1, 2, 3, 4], "Filtering and chaining should remove None and return list"

def test_maybe_chain_with_none():
    result = Maybe(None).filter(lambda x: x is not None).done()  # Using done
    assert result is None, "Chaining with None should return None"
