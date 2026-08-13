"""Neo4j driver gateway.

Follows the pattern of the other client modules in this package: a lazily
created, ``@lru_cache``-memoized handle built from ``app.config``, with the
driver import kept inside the functions so importing this module never requires
the package to be installed.

The driver holds its own connection pool, so there is no equivalent of
``MySQLPool`` here — one driver per process is the vendor's own guidance.

Two session helpers, and the distinction is load-bearing:

``read_session``  opens with ``default_access_mode=READ``. Retrieval uses this
                  and only this. Neo4j Community has no role-based access
                  control, so a read-only *user* cannot be created; the read
                  boundary is therefore enforced in application code — by this
                  helper, by the fixed query-template registry, and by tests
                  asserting no template writes. Recorded as a real limitation
                  rather than an equivalent control.
``write_session`` opens with write access. Reserved for ingestion-side
                  projection and schema work.
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Iterator

from app.config import get_settings

if TYPE_CHECKING:
    from neo4j import Driver, Session

logger = logging.getLogger(__name__)


@lru_cache
def get_graph_driver() -> "Driver":
    """The process-wide Neo4j driver. Not verified on creation — connectivity is
    a runtime concern the health probe and each caller's fail-open path own,
    exactly as the Qdrant client is built without a round-trip."""
    from neo4j import GraphDatabase

    settings = get_settings()
    return GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
        connection_timeout=settings.neo4j_connection_timeout,
    )


@contextmanager
def read_session(**kwargs: Any) -> Iterator["Session"]:
    """A read-only session against the configured database."""
    from neo4j import READ_ACCESS

    settings = get_settings()
    with get_graph_driver().session(
        database=settings.neo4j_database, default_access_mode=READ_ACCESS, **kwargs
    ) as session:
        yield session


@contextmanager
def write_session(**kwargs: Any) -> Iterator["Session"]:
    """A writable session. Ingestion and schema work only."""
    from neo4j import WRITE_ACCESS

    settings = get_settings()
    with get_graph_driver().session(
        database=settings.neo4j_database, default_access_mode=WRITE_ACCESS, **kwargs
    ) as session:
        yield session


def graph_available() -> bool:
    """Whether Neo4j answered. Never raises: every caller of the knowledge layer
    is expected to degrade rather than fail, so reachability is a value."""
    try:
        get_graph_driver().verify_connectivity()
        return True
    except Exception:
        logger.debug("Neo4j is not reachable.", exc_info=True)
        return False


def reset_graph_driver() -> None:
    """Close and forget the driver. For tests and for config changes in a
    long-lived process; the next call rebuilds it.

    Only closes a driver that was actually built — calling ``get_graph_driver``
    to close it would otherwise construct one just to throw it away.
    """
    if get_graph_driver.cache_info().currsize:
        try:
            get_graph_driver().close()
        except Exception:
            logger.debug("Closing the Neo4j driver failed.", exc_info=True)
    get_graph_driver.cache_clear()
