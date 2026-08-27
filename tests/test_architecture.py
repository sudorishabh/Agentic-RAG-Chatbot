"""The layering rules, asserted rather than described.

``app/README.md`` draws the dependency hierarchy. This is the same statement in
executable form, so the drawing cannot quietly stop being true.

Three properties are checked:

1. **No runtime import goes up a layer.** A module-level ``import`` creates real
   coupling and a real import-order constraint; those may only point down.
2. **Deferred upward imports are an allowlist.** A lazy (in-function) or
   ``TYPE_CHECKING`` import creates no runtime coupling, so it is a legitimate
   escape hatch — but a *new* one should be a decision someone made on purpose,
   not something that appeared. Each entry below records why it is allowed.
3. **Every package documents itself.** A directory with no ``__init__.py``
   docstring is a folder whose reason for existing is not written down.

The distinction in (1) versus (2) is the whole point. Measured before this test
existed: the package graph looked cyclic, and every apparent cycle turned out to
be either ``app.config`` (a leaf that everything reads) or an import that was
already deferred. Collapsing those two cases into one "dependency" is what made
the architecture unreadable.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

APP = pathlib.Path(__file__).resolve().parent.parent / "app"

#: Layer number per top-level package. A runtime import may target the same
#: layer or a lower one, never a higher one.
#:
#: ``config`` is 0 because it is a pure leaf: it imports nothing from the
#: application and everything reads it. ``(entry)`` is the top because
#: ``main``/``ingest_main``/``app_factory`` compose the app and nothing imports
#: them.
LAYERS: dict[str, int] = {
    "config": 0,
    "observability": 1,
    "core": 2,
    "schemas": 2,
    "catalog": 3,
    "cache": 3,
    "knowledge": 4,
    "ingestion": 5,
    "retrieval": 5,
    "generation": 6,
    "pipeline": 7,
    "workers": 7,
    "api": 8,
    "(entry)": 9,
}

#: Upward imports that are allowed *because they are deferred* — imported inside
#: a function body or under ``TYPE_CHECKING``, so no runtime coupling and no
#: import-order constraint exists. Value is the reason.
ALLOWED_DEFERRED_UPWARD: dict[tuple[str, str], str] = {
    ("catalog", "ingestion"):
        "TYPE_CHECKING only: date_decisions annotates its row with the decision "
        "type ingestion owns. The store shapes the row; the domain names it.",
    ("catalog", "knowledge"):
        "mentions.py annotates with knowledge.types.Mention (TYPE_CHECKING); "
        "entities.py calls knowledge.normalize inside a function. Persistence "
        "must not import a domain package at runtime.",
    ("generation", "retrieval"):
        "prompts.py lazily reads reranker.derived_authority to describe source "
        "authority in the prompt. A ranking concept generation only borrows.",
}

#: Packages exempt from the docstring requirement, with a reason.
DOCSTRING_EXEMPT = {
    "api": "router modules are self-describing; the package marker predates this rule",
    "core": "namespace only — the documented units are core.clients and core.models",
}


def _package_of(path: pathlib.Path) -> str:
    rel = path.relative_to(APP)
    return rel.parts[0] if len(rel.parts) > 1 else "(entry)"


def _target_package(module: str) -> str | None:
    """Which layer an ``app.*`` module name belongs to."""
    parts = module.split(".")
    if len(parts) < 2:
        return None
    head = parts[1]
    if (APP / head).is_dir():
        return head
    return "config" if head == "config" else "(entry)"


def _imports(path: pathlib.Path):
    """Yield (module, lineno, deferred) for every ``app.*`` import in a file."""
    found: list[tuple[str, int, bool]] = []

    def walk(node, deferred):
        for child in ast.iter_child_nodes(node):
            child_deferred = deferred
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                child_deferred = True
            elif isinstance(child, ast.If):
                names = {n.id for n in ast.walk(child.test) if isinstance(n, ast.Name)}
                names |= {n.attr for n in ast.walk(child.test)
                          if isinstance(n, ast.Attribute)}
                if "TYPE_CHECKING" in names:
                    child_deferred = True
            if isinstance(child, ast.Import):
                mods = [a.name for a in child.names]
            elif isinstance(child, ast.ImportFrom) and child.level == 0 and child.module:
                mods = [child.module]
            else:
                mods = []
            for m in mods:
                if m == "app" or m.startswith("app."):
                    found.append((m, child.lineno, deferred))
            walk(child, child_deferred)

    walk(ast.parse(path.read_text(encoding="utf-8")), False)
    return found


def _edges():
    """(source pkg, target pkg, file, lineno, deferred) for every app import."""
    for path in sorted(APP.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        source = _package_of(path)
        for module, lineno, deferred in _imports(path):
            target = _target_package(module)
            if target is None or target == source:
                continue
            yield source, target, path.relative_to(APP).as_posix(), lineno, deferred


def test_every_package_has_a_known_layer():
    """A new top-level package must be placed in the hierarchy deliberately."""
    packages = {p.name for p in APP.iterdir()
                if p.is_dir() and p.name != "__pycache__"}
    unplaced = sorted(packages - set(LAYERS))
    assert unplaced == [], (
        f"packages with no declared layer: {unplaced}. Add them to LAYERS in "
        f"this file and to the hierarchy in app/README.md."
    )


def test_no_runtime_import_goes_up_a_layer():
    """Module-level imports are real coupling; they may only point downward."""
    violations = []
    for source, target, file, lineno, deferred in _edges():
        if deferred:
            continue
        if LAYERS.get(target, 99) > LAYERS.get(source, -1):
            violations.append(
                f"{file}:{lineno}  {source}(L{LAYERS.get(source)}) -> "
                f"{target}(L{LAYERS.get(target)})"
            )
    assert violations == [], (
        "runtime imports pointing up the hierarchy:\n  "
        + "\n  ".join(violations)
        + "\n\nEither move the shared piece down (app/core is the usual home, "
          "see app/core/corpus.py for the pattern), or defer the import into a "
          "function and add it to ALLOWED_DEFERRED_UPWARD with a reason."
    )


def test_deferred_upward_imports_are_the_expected_set():
    """A deferred upward import is allowed, but not by accident."""
    seen = set()
    for source, target, _file, _lineno, deferred in _edges():
        if deferred and LAYERS.get(target, 99) > LAYERS.get(source, -1):
            seen.add((source, target))
    unexpected = sorted(seen - set(ALLOWED_DEFERRED_UPWARD))
    assert unexpected == [], (
        f"new deferred upward dependencies: {unexpected}. They create no runtime "
        f"coupling, so this is not a failure of correctness — but record the "
        f"reason in ALLOWED_DEFERRED_UPWARD so the next reader knows it was "
        f"intended."
    )


def test_no_runtime_dependency_cycles_between_packages():
    """Two packages that import each other at runtime cannot be understood apart."""
    runtime: set[tuple[str, str]] = set()
    for source, target, _file, _lineno, deferred in _edges():
        if not deferred:
            runtime.add((source, target))
    cycles = sorted({tuple(sorted(pair)) for pair in runtime
                     if (pair[1], pair[0]) in runtime})
    assert cycles == [], f"runtime import cycles: {cycles}"


@pytest.mark.parametrize(
    "package",
    sorted(p.name for p in APP.iterdir() if p.is_dir() and p.name != "__pycache__"),
)
def test_every_package_says_what_it_is_for(package):
    """``__init__.py`` is where a directory explains why it exists."""
    if package in DOCSTRING_EXEMPT:
        pytest.skip(DOCSTRING_EXEMPT[package])
    init = APP / package / "__init__.py"
    assert init.exists(), f"app/{package}/ has no __init__.py"
    doc = ast.get_docstring(ast.parse(init.read_text(encoding="utf-8")))
    assert doc and len(doc.strip()) > 40, (
        f"app/{package}/__init__.py needs a docstring saying what the package is "
        f"responsible for and how it relates to its neighbours."
    )
