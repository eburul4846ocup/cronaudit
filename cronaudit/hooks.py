"""Hook system for cronaudit — run callbacks before/after audits."""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any

# Valid lifecycle event names
EVENT_PRE_AUDIT = "pre_audit"
EVENT_POST_AUDIT = "post_audit"
EVENT_ON_ERROR = "on_error"

VALID_EVENTS = {EVENT_PRE_AUDIT, EVENT_POST_AUDIT, EVENT_ON_ERROR}

HookFn = Callable[..., None]


@dataclass
class HookRegistry:
    """Registry that stores and dispatches lifecycle hooks."""
    _hooks: Dict[str, List[HookFn]] = field(default_factory=dict, init=False, repr=False)

    def register(self, event: str, fn: HookFn) -> None:
        """Register a callback for the given event name."""
        if event not in VALID_EVENTS:
            raise ValueError(f"Unknown event '{event}'. Valid events: {sorted(VALID_EVENTS)}")
        self._hooks.setdefault(event, []).append(fn)

    def dispatch(self, event: str, **kwargs: Any) -> None:
        """Call all callbacks registered for *event*, passing kwargs."""
        for fn in self._hooks.get(event, []):
            fn(**kwargs)

    def clear(self, event: str | None = None) -> None:
        """Remove all hooks for *event*, or all hooks if event is None."""
        if event is None:
            self._hooks.clear()
        else:
            self._hooks.pop(event, None)

    def registered(self, event: str) -> List[HookFn]:
        """Return a copy of the callback list for *event*."""
        return list(self._hooks.get(event, []))


# Module-level default registry
_default_registry = HookRegistry()


def register(event: str, fn: HookFn) -> None:
    """Register a hook on the default registry."""
    _default_registry.register(event, fn)


def dispatch(event: str, **kwargs: Any) -> None:
    """Dispatch an event on the default registry."""
    _default_registry.dispatch(event, **kwargs)


def clear(event: str | None = None) -> None:
    """Clear hooks on the default registry."""
    _default_registry.clear(event)
