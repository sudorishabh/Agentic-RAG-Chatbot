"""What scope a query carries, and whether the graph may honour it.

Removing RBAC/ACL removed *permission* filtering. It did not remove legitimate
query scoping: a user who asks about PDFs, or about one theme, or about a date
range, has narrowed the question, and an answer drawn from outside that scope is
wrong even though nobody's permissions were violated.

The graph templates take an ``entity_id`` and, for historical queries, a date.
They express **no** notion of source type, theme, tag, language, document id or
effective date. So a scoped question cannot currently be answered from the
graph without discarding the scope, and discarding it silently is the failure
this module exists to prevent.

Fail closed
-----------
``SUPPORTED_SCOPE_KEYS`` is empty. Every scope key is therefore unsupported, and
a scoped query falls back to existing retrieval. That is deliberate: the default
answer to "can the graph honour this constraint?" is no, and a key becomes
supported only when a template genuinely implements it and a test proves the
result matches existing retrieval's semantics for that key.

Anything unparseable counts as a scope too. A condition shape this module does
not recognise is treated as an unsupported constraint rather than as no
constraint, so a new filter type cannot quietly disable the check.

Why not filter the evidence instead
-----------------------------------
It would be easy to pass a source-type condition into the Qdrant hydration step
and call the scope honoured. It would also be wrong. Hydration fetches the
*evidence* for facts the traversal already selected, so filtering it would still
assert a relationship read from an out-of-scope document — merely without
showing the passage. The scope has to constrain which facts are eligible, not
which quotes are displayed, and no template does that today.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Iterable

logger = logging.getLogger(__name__)

# Scope keys a graph template can honour with semantics equivalent to existing
# retrieval. Empty by design — see the module docstring. Adding a key here
# without a template that implements it reintroduces exactly the silent
# scope-dropping this guards against.
SUPPORTED_SCOPE_KEYS: frozenset[str] = frozenset()

# The pseudo-key used for the `source_type` argument, which arrives separately
# from the filter list but scopes the query just as much.
SOURCE_TYPE_KEY = "source_type"

# Marker for a condition whose shape we could not read.
UNKNOWN_KEY = "<unparsed-condition>"


@dataclass(frozen=True)
class QueryScope:
    """The constraints a query carries, reduced to payload keys."""

    keys: frozenset[str] = frozenset()
    source_type: str | None = None
    details: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_empty(self) -> bool:
        return not self.keys

    @property
    def unsupported(self) -> frozenset[str]:
        return frozenset(self.keys - SUPPORTED_SCOPE_KEYS)

    @property
    def is_supported(self) -> bool:
        """Whether every constraint can be honoured by the graph."""
        return not self.unsupported

    def describe(self) -> str:
        if self.is_empty:
            return "no scope"
        return ", ".join(sorted(self.keys))


def _condition_keys(condition: Any, depth: int = 0) -> Iterable[str]:
    """Payload keys a Qdrant condition constrains, recursively.

    Nested `Filter` objects are walked, because a scope hidden inside a
    `should` branch scopes the query just as much as a top-level one.
    """
    if condition is None or depth > 6:
        return
    key = getattr(condition, "key", None)
    if isinstance(key, str) and key:
        yield key
        return
    # A nested Filter: walk every branch.
    branches = (
        getattr(condition, "must", None),
        getattr(condition, "should", None),
        getattr(condition, "must_not", None),
        getattr(condition, "min_should", None),
    )
    seen_branch = False
    for branch in branches:
        if branch is None:
            continue
        seen_branch = True
        items = branch if isinstance(branch, (list, tuple)) else [branch]
        for item in items:
            yield from _condition_keys(item, depth + 1)
    if not seen_branch:
        # Not a keyed condition and not a filter we recognise — e.g. HasIdCondition,
        # which restricts to specific points and is very much a scope.
        yield UNKNOWN_KEY


def describe(
    filters: Any = None, source_type: str | None = None
) -> QueryScope:
    """Reduce a query's filters and source pin to a scope description."""
    keys: set[str] = set()
    details: list[str] = []

    if source_type:
        keys.add(SOURCE_TYPE_KEY)
        details.append(f"source_type={source_type}")

    if filters:
        items = filters if isinstance(filters, (list, tuple)) else [filters]
        for condition in items:
            try:
                found = list(_condition_keys(condition))
            except Exception:
                # Fail closed: an unreadable condition is a constraint we cannot
                # prove the graph honours.
                logger.debug("Unreadable filter condition.", exc_info=True)
                found = [UNKNOWN_KEY]
            if not found:
                found = [UNKNOWN_KEY]
            keys.update(found)
            details.extend(found)

    return QueryScope(
        keys=frozenset(keys), source_type=source_type,
        details=tuple(sorted(set(details))),
    )
