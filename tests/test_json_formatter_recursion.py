# tests/test_json_formatter_recursion.py
import json
import logging
import contextvars

from _Internal.Logging.Formatters import JSONLogFormatter


class FakeVar:
    def __init__(self, name: str):
        self.name = name

class FakeCtx:
    """Minimal stand-in for contextvars.Context used by _extract_generic_context()."""
    def __init__(self, mapping):
        # mapping: {FakeVar: value}
        self._mapping = mapping

    def __iter__(self):
        # The code does: for var in ctx:
        return iter(self._mapping.keys())

    def get(self, var):
        # The code does: ctx.get(var)
        return self._mapping[var]

def make_record(msg="hello"):
    return logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=(),
        exc_info=None,
    )

def make_formatter(deployed=False, traced=False):
    # No coloring/highlighting needed in test; formatter.format() returns a string
    return JSONLogFormatter(
        env_metadata={},
        forced_color=False,
        highlight_func=lambda s: s,
        traced=traced,
        deployed=deployed,
    )

def test_recursion_on_cyclic_context(monkeypatch):
    """Cyclic dict in context should not raise RecursionError and should still extract keys in shallow levels."""
    # Build a cyclic structure
    cyclic = {}
    cyclic["loop"] = cyclic
    cyclic["user_id"] = "u-123"  # one of the recognized keys

    fake_vars = {FakeVar("wrapper"): cyclic}
    fake_ctx = FakeCtx(fake_vars)

    # Monkeypatch copy_context to return our fake, cyclic-bearing context
    monkeypatch.setattr(contextvars, "copy_context", lambda: fake_ctx)

    fmt = make_formatter(deployed=False)
    out = fmt.format(make_record("hi"))

    # Should be valid JSON string
    payload = json.loads(out)

    assert payload["message"] == "hi"
    # Context should exist and include the discovered user_id
    assert "context" in payload
    assert payload["context"].get("user_id") == "u-123"

def test_depth_limit_prevents_deep_scan(monkeypatch):
    """Very deep nesting beyond depth limit should not blow up and should skip too-deep keys."""
    # Build a deeply nested dict: wrapper -> nested -> nested ... (100 levels) -> organization_id
    deep = {}
    curr = deep
    for _ in range(100):
        nxt = {}
        curr["nested"] = nxt
        curr = nxt
    curr["organization_id"] = "org-1"  # recognized key, but too deep

    fake_vars = {FakeVar("wrapper"): deep}
    fake_ctx = FakeCtx(fake_vars)
    monkeypatch.setattr(contextvars, "copy_context", lambda: fake_ctx)

    fmt = make_formatter(deployed=True)  # deployed=True gives minified JSON; also tests that path
    out = fmt.format(make_record("deep"))

    payload = json.loads(out)
    assert payload["message"] == "deep"
    assert "context" not in payload

def test_handles_objects_with___dict___and_cycles(monkeypatch):
    """Objects with __dict__ and self-references should be safe under the recursion guard."""
    class Node:
        def __init__(self, name):
            self.name = name
            self.child = None

    a = Node("a")
    b = Node("b")
    a.child = b
    b.child = a  # cycle
    # Put a recognized key in a shallow attribute to verify extraction
    a.user_id = "user-xyz"

    fake_vars = {FakeVar("root"): a}
    fake_ctx = FakeCtx(fake_vars)
    monkeypatch.setattr(contextvars, "copy_context", lambda: fake_ctx)

    fmt = make_formatter()
    out = fmt.format(make_record("obj graph"))

    payload = json.loads(out)
    assert payload["message"] == "obj graph"
    assert "context" in payload
    assert payload["context"].get("user_id") == "user-xyz"
