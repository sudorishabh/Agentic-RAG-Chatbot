"""The ingestion control plane must not be callable by anyone who can reach it.

Every route was open, including when `auth_enabled` was true — `require_principal`
was applied to /chat and /search and to nothing else. Exposed without credentials:
a corpus-wide crawl, arbitrary content injection into the answer set, a reindex,
and a log carrying internal ids, titles, source URLs and error strings.

Authentication is now on by default and gated on its own switch, because the
deployment that has not enabled retrieval auth is exactly the one that would
otherwise leave these open. Authorization is per route: reading needs an
identity, mutating needs the operations group.

No MySQL, no Qdrant, no network — the work behind each route is stubbed and
asserted to be unreachable when the request is rejected.
"""

from __future__ import annotations

import time

import pytest

jwt = pytest.importorskip("jwt")  # PyJWT ships with the auth feature

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import get_settings

SECRET = "test-secret"
ADMIN = "ingest-admin"

# Every route on the control plane, and how to call it.
MUTATING = [
    ("post", "/ingest/run", {}),
    ("post", "/ingest/article", {"title": "T", "body": "B"}),
    ("post", "/reindex", {"document_id": "doc-1"}),
]
READ_ONLY = [("get", "/ingest/log", None)]
ALL_ROUTES = MUTATING + READ_ONLY


class _Work:
    """Records whether a route's actual work was reached."""

    def __init__(self) -> None:
        self.calls: list[str] = []


@pytest.fixture
def work(monkeypatch) -> _Work:
    done = _Work()

    import app.api.ingest as ingest_api
    from app.catalog import log as ingest_log
    from app.workers import tasks

    monkeypatch.setattr(
        tasks, "ingest_drupal",
        lambda bundles=None, reconcile=False: done.calls.append("crawl") or {},
    )
    monkeypatch.setattr(
        tasks, "reindex_document",
        lambda document_id, source_type="website": (
            done.calls.append("reindex") or {"document_id": document_id, "status": "queued"}
        ),
    )
    monkeypatch.setattr(
        ingest_api, "ingest_article",
        lambda **kw: (done.calls.append("article"), ("doc-1", 3))[1],
    )
    monkeypatch.setattr(
        ingest_log, "recent",
        lambda **kw: done.calls.append("log") or [],
    )
    return done


@pytest.fixture
def client(monkeypatch) -> TestClient:
    """The ingestion app, protected as it ships: auth on, an admin group set."""
    settings = get_settings()
    monkeypatch.setattr(settings, "ingest_auth_enabled", True)
    monkeypatch.setattr(settings, "ingest_admin_group", ADMIN)
    monkeypatch.setattr(settings, "ops_admin_group", "")
    monkeypatch.setattr(settings, "jwt_secret", SECRET)
    monkeypatch.setattr(settings, "jwt_algorithms", "HS256")
    monkeypatch.setattr(settings, "jwt_audience", "")
    monkeypatch.setattr(settings, "jwt_issuer", "")
    # Deliberately off: the ingestion switch must protect these routes on its
    # own, on a deployment whose public API is anonymous.
    monkeypatch.setattr(settings, "auth_enabled", False)

    from app.api.ingest import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _token(groups: list[str], *, ttl: int = 60) -> str:
    return jwt.encode(
        {"groups": groups, "exp": int(time.time()) + ttl}, SECRET, algorithm="HS256"
    )


def _call(client: TestClient, method: str, path: str, body, token: str | None = None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    if method == "get":
        return client.get(path, headers=headers)
    return client.post(path, json=body, headers=headers)


# --------------------------------------------------------------------------- #
# Authentication: no identity, no ingestion.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("method,path,body", ALL_ROUTES)
def test_an_unauthenticated_request_is_rejected(client, work, method, path, body):
    response = _call(client, method, path, body)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert work.calls == [], "the work behind the route must not run"


@pytest.mark.parametrize("method,path,body", ALL_ROUTES)
def test_a_garbage_token_is_rejected(client, work, method, path, body):
    assert _call(client, method, path, body, token="not-a-jwt").status_code == 401
    assert work.calls == []


@pytest.mark.parametrize("method,path,body", ALL_ROUTES)
def test_an_expired_token_is_rejected(client, work, method, path, body):
    expired = _token([ADMIN], ttl=-30)

    assert _call(client, method, path, body, token=expired).status_code == 401
    assert work.calls == []


def test_a_token_signed_with_another_key_is_rejected(client, work):
    forged = jwt.encode(
        {"groups": [ADMIN], "exp": int(time.time()) + 60}, "other-secret", algorithm="HS256"
    )

    assert _call(client, "post", "/ingest/run", {}, token=forged).status_code == 401
    assert work.calls == []


# --------------------------------------------------------------------------- #
# Authorization: mutating the corpus needs the operations group.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("method,path,body", MUTATING)
def test_a_non_admin_cannot_change_the_corpus(client, work, method, path, body):
    response = _call(client, method, path, body, token=_token(["public"]))

    assert response.status_code == 403
    assert ADMIN in response.json()["detail"]
    assert work.calls == []


@pytest.mark.parametrize("method,path,body", MUTATING)
def test_an_admin_may_change_the_corpus(client, work, method, path, body):
    response = _call(client, method, path, body, token=_token([ADMIN, "public"]))

    assert response.status_code == 200
    assert work.calls, "the route did its work"


def test_reading_the_log_needs_an_identity_but_not_the_group(client, work):
    """The log is not a mutation, and an operator without deploy rights should
    still be able to see why a document failed. It is not public, though — it
    carries internal ids, source URLs and error strings."""
    response = _call(client, "get", "/ingest/log", None, token=_token(["public"]))

    assert response.status_code == 200
    assert work.calls == ["log"]


# --------------------------------------------------------------------------- #
# The switch, and what it means when it is off or half-configured.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("method,path,body", ALL_ROUTES)
def test_disabling_ingest_auth_opens_the_routes_again(client, work, monkeypatch, method, path, body):
    """The documented escape hatch for an ingestion server on a private
    interface. Off is a deliberate act, not the default."""
    monkeypatch.setattr(get_settings(), "ingest_auth_enabled", False)

    assert _call(client, method, path, body).status_code == 200
    assert work.calls


def test_the_default_is_protected():
    """A fresh Settings object — what a deployment gets with nothing set."""
    from app.config import Settings

    assert Settings(_env_file=None).ingest_auth_enabled is True


@pytest.mark.parametrize("method,path,body", MUTATING)
def test_without_a_configured_group_any_authenticated_caller_may_mutate(
    client, work, monkeypatch, method, path, body
):
    """The check has nothing to compare against, so it cannot be enforced —
    the group is logged as missing rather than treated as satisfied silently
    or as denying everyone (which would brick the control plane)."""
    monkeypatch.setattr(get_settings(), "ingest_admin_group", "")
    monkeypatch.setattr(get_settings(), "ops_admin_group", "")

    assert _call(client, method, path, body, token=_token(["public"])).status_code == 200
    assert work.calls


def test_the_ops_admin_group_is_the_fallback(client, work, monkeypatch):
    """A deployment that already names an operations group need not name a
    second one."""
    monkeypatch.setattr(get_settings(), "ingest_admin_group", "")
    monkeypatch.setattr(get_settings(), "ops_admin_group", "ops")

    assert _call(client, "post", "/ingest/run", {}, token=_token(["public"])).status_code == 403
    assert _call(client, "post", "/ingest/run", {}, token=_token(["ops"])).status_code == 200


def test_a_missing_secret_denies_rather_than_opens(client, work, monkeypatch):
    """Misconfiguration must fail closed: auth required, no key to verify with,
    nothing gets through."""
    monkeypatch.setattr(get_settings(), "jwt_secret", "")

    response = _call(client, "post", "/ingest/run", {}, token=_token([ADMIN]))

    assert response.status_code == 500
    assert work.calls == []


# --------------------------------------------------------------------------- #
# The retrieval API is unchanged: no document-level access control was added.
# --------------------------------------------------------------------------- #

def test_retrieval_auth_is_untouched_by_the_ingestion_switch(monkeypatch):
    """`ingest_auth_enabled` governs the control plane only. /chat and /search
    still follow `auth_enabled`, and groups still do not scope the corpus."""
    from app.api.auth import Principal, require_principal

    settings = get_settings()
    monkeypatch.setattr(settings, "ingest_auth_enabled", True)
    monkeypatch.setattr(settings, "auth_enabled", False)

    principal = require_principal(credentials=None)

    assert isinstance(principal, Principal)
    assert principal.groups == ["public"], "anonymous retrieval is unchanged"
