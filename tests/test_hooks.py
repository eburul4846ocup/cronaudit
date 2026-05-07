"""Tests for cronaudit.hooks."""

import pytest
from cronaudit.hooks import (
    HookRegistry,
    EVENT_PRE_AUDIT,
    EVENT_POST_AUDIT,
    EVENT_ON_ERROR,
    register,
    dispatch,
    clear,
)


# --- HookRegistry ---

def test_register_and_dispatch_calls_fn():
    reg = HookRegistry()
    called_with = {}
    reg.register(EVENT_PRE_AUDIT, lambda server: called_with.update({"server": server}))
    reg.dispatch(EVENT_PRE_AUDIT, server="web1")
    assert called_with["server"] == "web1"


def test_multiple_hooks_for_same_event():
    reg = HookRegistry()
    log = []
    reg.register(EVENT_POST_AUDIT, lambda **kw: log.append("a"))
    reg.register(EVENT_POST_AUDIT, lambda **kw: log.append("b"))
    reg.dispatch(EVENT_POST_AUDIT)
    assert log == ["a", "b"]


def test_dispatch_unknown_event_does_nothing():
    reg = HookRegistry()
    # no hooks registered — should not raise
    reg.dispatch(EVENT_ON_ERROR, error="oops")


def test_register_invalid_event_raises():
    reg = HookRegistry()
    with pytest.raises(ValueError, match="Unknown event"):
        reg.register("bad_event", lambda: None)


def test_clear_specific_event():
    reg = HookRegistry()
    log = []
    reg.register(EVENT_PRE_AUDIT, lambda **kw: log.append("pre"))
    reg.register(EVENT_POST_AUDIT, lambda **kw: log.append("post"))
    reg.clear(EVENT_PRE_AUDIT)
    reg.dispatch(EVENT_PRE_AUDIT)
    reg.dispatch(EVENT_POST_AUDIT)
    assert log == ["post"]


def test_clear_all_events():
    reg = HookRegistry()
    log = []
    reg.register(EVENT_PRE_AUDIT, lambda **kw: log.append(1))
    reg.register(EVENT_POST_AUDIT, lambda **kw: log.append(2))
    reg.clear()
    reg.dispatch(EVENT_PRE_AUDIT)
    reg.dispatch(EVENT_POST_AUDIT)
    assert log == []


def test_registered_returns_copy():
    reg = HookRegistry()
    fn = lambda **kw: None  # noqa: E731
    reg.register(EVENT_PRE_AUDIT, fn)
    lst = reg.registered(EVENT_PRE_AUDIT)
    assert fn in lst
    # mutating the returned list does not affect registry
    lst.clear()
    assert len(reg.registered(EVENT_PRE_AUDIT)) == 1


def test_registered_empty_for_unknown_event():
    reg = HookRegistry()
    assert reg.registered(EVENT_ON_ERROR) == []


# --- module-level helpers ---

def test_module_level_register_and_dispatch():
    clear()  # reset default registry
    log = []
    register(EVENT_POST_AUDIT, lambda **kw: log.append(kw.get("server")))
    dispatch(EVENT_POST_AUDIT, server="srv1")
    assert log == ["srv1"]
    clear()


def test_module_level_clear_resets_hooks():
    clear()
    log = []
    register(EVENT_PRE_AUDIT, lambda **kw: log.append(1))
    clear()
    dispatch(EVENT_PRE_AUDIT)
    assert log == []
