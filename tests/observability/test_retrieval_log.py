"""What a retrieval trace must guarantee, asserted rather than described.

Four properties, in the order they matter:

1. **Off means off.** With ``is_retrieval_log`` unset nothing is built and
   nothing is written — the property the whole design of the API rests on.
2. **On means complete.** One file per query, holding every retriever's request,
   results, latency and failure, plus the context that reached the LLM.
3. **Nothing sensitive, nothing unbounded.** Secrets are redacted by key and
   every string is clipped.
4. **A logging failure is not a query failure.** An unwritable directory costs
   the trace and nothing else.

Qdrant, Neo4j and MySQL are all stubbed: these tests are about the trace, so
they must not need a running store.
"""
from __future__ import annotations

import json
import threading

import pytest

from app.observability import retrieval_log as retlog
from app.observability.retrieval_log import naming, safe, sink, sql, views


@pytest.fixture
def logging_on(monkeypatch, tmp_path):
    """Retrieval logging enabled, writing into a temporary directory."""
    from app.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "is_retrieval_log", True, raising=False)
    monkeypatch.setattr(settings, "retrieval_log_dir", str(tmp_path), raising=False)
    monkeypatch.setattr(settings, "retrieval_log_summary", True, raising=False)
    monkeypatch.setattr(settings, "retrieval_log_include_text", True, raising=False)
    monkeypatch.setattr(settings, "retrieval_log_max_results", 3, raising=False)
    monkeypatch.setattr(settings, "retrieval_log_max_text_chars", 50, raising=False)
    monkeypatch.setattr(settings, "retrieval_log_detail", "compact", raising=False)
    return tmp_path


@pytest.fixture
def full_detail(logging_on, monkeypatch):
    """The structured rendering: every field, for programmatic analysis."""
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "retrieval_log_detail", "full", raising=False)
    return logging_on


def _traces(root):
    """Every trace under ``root``, excluding the errors/ copies."""
    return sorted(p for p in root.rglob("*/trace.json") if "errors" not in p.parts)


def _only_trace(root):
    files = _traces(root)
    assert len(files) == 1, f"expected one trace, found {files}"
    return json.loads(files[0].read_text(encoding="utf-8"))


def _only_report(root):
    files = sorted(p for p in root.rglob("*/report.md") if "errors" not in p.parts)
    assert len(files) == 1, f"expected one report, found {files}"
    return files[0].read_text(encoding="utf-8")


# -- 1. off means off -------------------------------------------------------
def test_disabled_writes_nothing_and_builds_nothing(monkeypatch, tmp_path):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "is_retrieval_log", False, raising=False)
    monkeypatch.setattr(get_settings(), "retrieval_log_dir", str(tmp_path), raising=False)

    def _explode() -> dict:  # the request description must never be built
        raise AssertionError("a disabled trace described its request")

    with retlog.query_log("who funds TERI?", entrypoint="test") as log:
        assert log is None
        assert retlog.active() is None
        with retlog.qdrant_call("vector_search", request=_explode) as call:
            call.qdrant_results([object()])
        retlog.note_context([object()])
        retlog.note_error("nowhere", RuntimeError("ignored"))

    assert list(tmp_path.rglob("*.json")) == []
    assert list(tmp_path.rglob("*.jsonl")) == []


def test_bound_is_the_identity_when_disabled(monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "is_retrieval_log", False, raising=False)

    def work() -> str:
        return "done"

    assert retlog.bound(work) is work


# -- 2. on means complete ---------------------------------------------------
class _Point:
    def __init__(self, id_, score, payload):
        self.id = id_
        self.score = score
        self.payload = payload


def test_a_query_writes_one_file_with_every_retriever(logging_on):
    with retlog.query_log(
        "which projects did TERI lead?", entrypoint="chat.stream", top_k=6
    ) as log:
        assert log is not None
        retlog.note_query(intent="qa", search_query="projects TERI lead")

        with retlog.qdrant_call(
            "vector_search",
            stage="dense_pull",
            request={"collection": "documents", "limit": 40},
        ) as call:
            call.qdrant_results(
                [
                    _Point("c1", 0.81, {"chunk_text": "TERI led the project.",
                                        "document_id": "d1", "title": "Annual Report"}),
                    _Point("c2", 0.55, {"chunk_text": "Unrelated.",
                                        "document_id": "d2"}),
                ]
            )

        with retlog.graph_call(
            "cypher_template",
            stage="graph_traversal",
            request={"template_id": "projects_led_by_person", "parameters": {"name": "A"}},
        ) as call:
            call.row_results([{"project_id": "p1", "status": "current"}])
            call.note(entities=["e1"], claims=["cl1"])

        with retlog.mysql_call(
            "select", stage="catalog", request={"sql": "SELECT 1", "tables": ["documents"]}
        ) as call:
            call.row_results([{"n": 3}])

        retlog.note_context(
            [
                type("B", (), {"n": 1, "text": "TERI led the project.", "score": 0.9,
                               "conflict": False,
                               "payload": {"document_id": "d1", "title": "AR"}})()
            ]
        )
        retlog.note_outcome(cached=False, answered=True, used_chunks=1)
        request_id = log.request_id

    trace = _only_trace(logging_on)
    assert trace["request_id"] == request_id
    assert trace["question"] == "which projects did TERI lead?"
    assert trace["entrypoint"] == "chat.stream"
    assert trace["top_k"] == 6
    assert trace["query"]["intent"] == "qa"
    # Every store is named once, with its own totals.
    assert trace["retrievers"]["invoked"] == ["graph", "mysql", "qdrant"]
    assert trace["retrievers"]["totals"]["qdrant"]["calls"] == 1
    assert trace["retrievers"]["totals"]["qdrant"]["results"] == 2
    assert trace["retrievers"]["totals"]["graph"]["stages"] == ["graph_traversal"]

    events = {(e["retriever"], e["stage"]): e for e in trace["events"]}
    qdrant = events[("qdrant", "dense_pull")]
    assert qdrant["request"]["collection"] == "documents"
    assert qdrant["result_count"] == 2
    # One line per hit: rank, score, provenance, snippet.
    assert qdrant["results"] == [
        " 1. 0.810  Annual Report · d1 | TERI led the project.",
        " 2. 0.550  d2 | Unrelated.",
    ]
    assert qdrant["latency_ms"] >= 0
    graph = events[("graph", "graph_traversal")]
    assert graph["results"] == ['{"project_id": "p1", "status": "current"}']
    assert graph["metrics"]["entities"] == ["e1"]
    assert events[("mysql", "catalog")]["results"] == ['{"n": 3}']

    # The context the LLM saw, and the timings, in the same file. Its text is
    # kept whole — it is the payload, not a sample of one.
    assert trace["context"]["block_count"] == 1
    assert trace["context"]["blocks"][0]["text"] == "TERI led the project."
    assert trace["context"]["blocks"][0]["source"] == "AR · d1"
    assert trace["outcome"]["answered"] is True
    assert trace["timings"]["total_latency_ms"] >= 0
    assert trace["timings"]["finished_at"]
    assert trace["errors"] == []


def test_the_day_directory_and_the_summary_line(logging_on):
    with retlog.query_log("how many reports?", entrypoint="search") as log:
        with retlog.mysql_call("select", stage="catalog") as call:
            call.row_results([{"n": 7}])
        day, request_id = log.day, log.request_id

    # The directory is named for the question and the time it was asked, not
    # for the request id — a uuid finds nothing.
    folder = next((logging_on / day).iterdir())
    assert folder.name.startswith("how many reports - ")
    assert (folder / "trace.json").is_file()
    assert (folder / "report.md").is_file()
    digest = (logging_on / "summary" / f"{day}.jsonl").read_text(encoding="utf-8")
    rows = [json.loads(line) for line in digest.splitlines()]
    assert len(rows) == 1
    assert rows[0]["request_id"] == request_id
    assert rows[0]["retrievers"] == ["mysql"]
    assert rows[0]["mysql_results"] == 1


def test_a_failure_is_recorded_and_copied_under_errors(logging_on):
    boom = RuntimeError("qdrant unreachable")
    with retlog.query_log("anything", entrypoint="test") as log:
        with pytest.raises(RuntimeError):
            with retlog.qdrant_call("vector_search", stage="dense_pull"):
                raise boom
        # A retriever that swallows its own failure still reports it.
        with retlog.qdrant_call("retrieve", stage="parent_fetch") as call:
            call.fail(ValueError("parent missing"))
        request_id = log.request_id
        day = log.day

    trace = _only_trace(logging_on)
    assert trace["events"][0]["error"]["type"] == "RuntimeError"
    assert trace["events"][0]["error"]["message"] == "qdrant unreachable"
    assert trace["events"][1]["error"]["type"] == "ValueError"
    # Findable without reading every file, under the same name.
    failed = next((logging_on / "errors" / day).iterdir())
    assert (failed / "trace.json").is_file()
    assert (failed / "report.md").is_file()


def test_a_pipeline_exception_is_recorded_and_re_raised(logging_on):
    with pytest.raises(ZeroDivisionError):
        with retlog.query_log("anything", entrypoint="test"):
            1 / 0

    trace = _only_trace(logging_on)
    assert trace["errors"][0]["type"] == "ZeroDivisionError"
    assert trace["errors"][0]["where"] == "pipeline"


def test_worker_threads_contribute_to_the_same_trace(logging_on):
    """The parallel search legs and the graph executor run off-thread; without
    `bound` their calls would be recorded nowhere."""

    def leg(name: str) -> None:
        with retlog.qdrant_call("vector_search", stage=name) as call:
            call.count_only(1)

    with retlog.query_log("parallel", entrypoint="test"):
        threads = [
            threading.Thread(target=retlog.bound(leg), args=(name,))
            for name in ("keyword_leg", "title_leg")
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    trace = _only_trace(logging_on)
    assert sorted(e["stage"] for e in trace["events"]) == ["keyword_leg", "title_leg"]


def test_concurrent_queries_each_get_their_own_file(logging_on):
    def one(index: int) -> None:
        with retlog.query_log(f"question {index}", entrypoint="test"):
            with retlog.qdrant_call("vector_search", stage="dense_pull") as call:
                call.count_only(index)

    threads = [threading.Thread(target=one, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    traces = _traces(logging_on)
    assert len(traces) == 8
    ids = {json.loads(p.read_text(encoding="utf-8"))["request_id"] for p in traces}
    assert len(ids) == 8
    digest = (logging_on / "summary").glob("*.jsonl")
    lines = sum(
        len(p.read_text(encoding="utf-8").splitlines()) for p in digest
    )
    assert lines == 8


# -- 3. nothing sensitive, nothing unbounded -------------------------------
@pytest.mark.parametrize(
    "key",
    ["password", "MYSQL_PASSWORD", "api_key", "apiKey", "access_token", "Authorization",
     "qdrant_api_key", "private_key", "session_id", "connection_string"],
)
def test_secret_shaped_keys_are_redacted(key):
    assert safe.jsonable({key: "hunter2"})[key] == safe.REDACTED


def test_a_harmless_key_is_kept():
    assert safe.jsonable({"theme": "Energy"}) == {"theme": "Energy"}


def test_redaction_reaches_nested_values(logging_on):
    with retlog.query_log("q", entrypoint="test"):
        with retlog.mysql_call("select", stage="catalog") as call:
            call.describe({"dsn": {"host": "db", "password": "p"}, "tables": ["documents"]})

    trace = _only_trace(logging_on)
    assert trace["events"][0]["request"]["dsn"] == safe.REDACTED


def test_every_string_is_clipped(full_detail):
    with retlog.query_log("q", entrypoint="test"):
        with retlog.qdrant_call("vector_search", stage="dense_pull") as call:
            call.qdrant_results(
                [_Point("c1", 0.5, {"chunk_text": "x" * 5000, "document_id": "d"})]
            )

    trace = _only_trace(full_detail)
    hit = trace["events"][0]["results"][0]
    assert hit["text"].endswith(safe.TRUNCATION_MARKER)
    assert len(hit["text"]) <= 50 + len(safe.TRUNCATION_MARKER)
    # The true size survives the truncation.
    assert hit["text_chars"] == 5000


def test_a_compact_hit_is_one_short_line(logging_on):
    with retlog.query_log("q", entrypoint="test"):
        with retlog.qdrant_call("vector_search", stage="dense_pull") as call:
            call.qdrant_results(
                [_Point("c1", 0.5, {"chunk_text": "x" * 5000, "document_id": "d"})]
            )

    line = _only_trace(logging_on)["events"][0]["results"][0]
    assert isinstance(line, str)
    assert "\n" not in line  # one line, whatever the passage looked like
    assert len(line) <= 80 + views.COMPACT_TEXT_CHARS + len(safe.TRUNCATION_MARKER)


def test_results_are_capped_but_the_count_is_true(logging_on):
    with retlog.query_log("q", entrypoint="test"):
        with retlog.qdrant_call("vector_search", stage="dense_pull") as call:
            call.qdrant_results(
                [_Point(f"c{i}", 0.5, {"chunk_text": "t"}) for i in range(10)]
            )

    event = _only_trace(logging_on)["events"][0]
    assert event["result_count"] == 10          # what Qdrant returned
    assert len(event["results"]) == 3           # what the trace kept
    assert event["results_truncated"] is True


def test_text_can_be_left_out_entirely(logging_on, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(
        get_settings(), "retrieval_log_include_text", False, raising=False
    )
    with retlog.query_log("q", entrypoint="test"):
        with retlog.qdrant_call("vector_search", stage="dense_pull") as call:
            call.qdrant_results([_Point("c1", 0.5, {"chunk_text": "secret-ish text"})])

    line = _only_trace(logging_on)["events"][0]["results"][0]
    assert "secret-ish" not in line
    assert line.endswith("15 chars")  # the reference to it remains


def test_text_can_be_left_out_of_the_full_rendering_too(full_detail, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(
        get_settings(), "retrieval_log_include_text", False, raising=False
    )
    with retlog.query_log("q", entrypoint="test"):
        with retlog.qdrant_call("vector_search", stage="dense_pull") as call:
            call.qdrant_results([_Point("c1", 0.5, {"chunk_text": "secret-ish text"})])

    hit = _only_trace(full_detail)["events"][0]["results"][0]
    assert "text" not in hit
    assert hit["text_chars"] == 15


def test_unserializable_values_do_not_break_a_trace(logging_on):
    class Awkward:
        def __repr__(self) -> str:
            return "<awkward>"

    with retlog.query_log("q", entrypoint="test"):
        with retlog.qdrant_call("vector_search", stage="dense_pull") as call:
            call.describe({"filter": Awkward()})

    assert _only_trace(logging_on)["events"][0]["request"]["filter"] == "<awkward>"


# -- 4. a logging failure is not a query failure ---------------------------
def test_an_unwritable_directory_costs_only_the_trace(monkeypatch, tmp_path):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "is_retrieval_log", True, raising=False)
    monkeypatch.setattr(get_settings(), "retrieval_log_dir", str(tmp_path), raising=False)
    monkeypatch.setattr(
        sink, "_dump", lambda *a, **k: (_ for _ in ()).throw(OSError("disk full"))
    )

    with retlog.query_log("q", entrypoint="test") as log:
        with retlog.qdrant_call("vector_search", stage="dense_pull") as call:
            call.count_only(1)
        assert log is not None  # the query carried on

    assert _traces(tmp_path) == []


def test_a_broken_serializer_costs_only_the_trace(monkeypatch, logging_on):
    with retlog.query_log("q", entrypoint="test") as log:
        monkeypatch.setattr(
            type(log), "to_dict", lambda self: (_ for _ in ()).throw(TypeError("nope"))
        )

    assert _traces(logging_on) == []


# -- the pieces, on their own ----------------------------------------------
def test_tables_are_read_off_a_statement():
    assert sql.tables_in(
        "SELECT s.* FROM `documents` s JOIN documents_theme t ON t.document_id = s.id"
    ) == ["documents", "documents_theme"]
    assert sql.statement_verb("  select 1") == "select"


class _FakeCursor:
    """Just enough of a pymysql DictCursor to drive the proxy."""

    def __init__(self, rows):
        self._rows = rows
        self.executed = []
        self.rowcount = len(rows)
        self.closed = False

    def execute(self, sql, args=None):
        self.executed.append((sql, args))
        return len(self._rows)

    def fetchall(self):
        return list(self._rows)

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


class _FakeConnection:
    def __init__(self, rows):
        self.rows = rows
        self.cursors = []
        self.committed = False

    def cursor(self, *args, **kwargs):
        cursor = _FakeCursor(self.rows)
        self.cursors.append(cursor)
        return cursor

    def commit(self):
        self.committed = True


def _mysql_gateway(monkeypatch, connection):
    """Point ``mysql_connection`` at a fake pool, keeping the real proxy logic."""
    import contextlib

    from app.core.clients import database

    class _Pool:
        @contextlib.contextmanager
        def connection(self):
            yield connection

    monkeypatch.setattr(database, "get_mysql_pool", lambda: _Pool())
    return database.mysql_connection


def test_the_mysql_gateway_traces_a_statement_it_never_had_to_be_told_about(
    logging_on, monkeypatch
):
    """The catalog's ~30 query sites are untouched: the connection gateway is
    what records the SQL, its parameters, its tables and its rows."""
    connection = _FakeConnection([{"document_id": "d1", "title": "Annual Report"}])
    mysql_connection = _mysql_gateway(monkeypatch, connection)

    with retlog.query_log("how many reports in 2024?", entrypoint="test"):
        with mysql_connection() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT s.* FROM `documents` s WHERE s.published_at >= %s",
                ("2024-01-01",),
            )
            rows = cur.fetchall()
        conn.commit()

    assert rows == [{"document_id": "d1", "title": "Annual Report"}]
    assert connection.committed  # the proxy delegates everything it does not own
    assert connection.cursors[0].closed  # ...including the cursor's own teardown

    event = _only_trace(logging_on)["events"][0]
    assert event["retriever"] == "mysql"
    assert event["operation"] == "select"
    assert event["request"]["tables"] == ["documents"]
    assert event["request"]["parameters"] == ["2024-01-01"]
    assert event["result_count"] == 1
    assert event["results"] == [
        '{"document_id": "d1", "title": "Annual Report"}'
    ]
    assert event["latency_ms"] >= 0


def test_the_mysql_gateway_hands_out_the_real_connection_when_disabled(
    monkeypatch
):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "is_retrieval_log", False, raising=False)
    connection = _FakeConnection([])
    mysql_connection = _mysql_gateway(monkeypatch, connection)

    with mysql_connection() as conn:
        assert conn is connection


def test_a_failing_statement_is_traced_and_still_raises(logging_on, monkeypatch):
    connection = _FakeConnection([])

    def boom(self, sql, args=None):
        raise RuntimeError("deadlock")

    monkeypatch.setattr(_FakeCursor, "execute", boom)
    mysql_connection = _mysql_gateway(monkeypatch, connection)

    with retlog.query_log("q", entrypoint="test"):
        with pytest.raises(RuntimeError):
            with mysql_connection() as conn, conn.cursor() as cur:
                cur.execute("SELECT 1")

    event = _only_trace(logging_on)["events"][0]
    assert event["error"]["type"] == "RuntimeError"
    assert event["error"]["message"] == "deadlock"


def test_the_report_explains_the_same_trace(logging_on):
    """``report.md`` is prose over the same record — no new data, and the
    standing explanation of what each stage is for."""
    with retlog.query_log("which projects did TERI lead?", entrypoint="chat.stream"):
        retlog.note_query(intent="qa", search_query="projects TERI lead")
        with retlog.qdrant_call(
            "vector_search", stage="website_pull",
            request={"collection": "documents", "limit": 20},
        ) as call:
            call.qdrant_results(
                [_Point("c1", 0.81, {"chunk_text": "TERI led the project.",
                                     "title": "Annual Report"})]
            )
        with retlog.mysql_call(
            "select", stage="catalog", request={"sql": "SELECT 1"}
        ) as call:
            call.row_results([{"n": 3}])
        retlog.note_context(
            [type("B", (), {"n": 1, "text": "TERI led the project.", "score": 0.9,
                            "conflict": False, "payload": {"title": "AR"}})()]
        )
        retlog.note_outcome(answered=True, used_chunks=1, citations=1, cached=False)

    report = _only_report(logging_on)
    # The question, and the record it belongs to.
    assert report.startswith("# which projects did TERI lead?")
    assert "`chat.stream`" in report
    # What was searched for, and how it was routed.
    assert "projects TERI lead" in report
    assert "answer from document content" in report      # the intent, explained
    # Each retriever named for what it holds, not for its technology.
    assert "vector search over the document chunks" in report
    assert "the document catalog" in report
    # The leg, explained — the thing a JSON field name cannot say.
    assert "the website half of the deliberately split pull" in report
    # The SQL, as SQL.
    assert "```sql" in report and "SELECT 1" in report
    # What the LLM was given, with the citation number it will carry.
    assert "## 4. What the LLM was given" in report
    assert "#### [1]" in report
    assert "> TERI led the project." in report
    assert "## 7. Failures" in report and "None." in report


def test_the_report_names_a_refusal_for_what_it_is(logging_on):
    """The case worth reading a trace for: retrieval worked, generation didn't."""
    with retlog.query_log("q", entrypoint="chat.stream"):
        retlog.note_context(
            [type("B", (), {"n": 1, "text": "relevant passage", "score": 0.9,
                            "conflict": False, "payload": {}})()]
        )
        retlog.note_outcome(answered=False, used_chunks=1, answer_chars=58)

    report = _only_report(logging_on)
    assert "**refused**" in report
    assert "which is a generation problem rather than a retrieval one" in report


def test_a_report_failure_still_leaves_the_trace(logging_on, monkeypatch):
    from app.observability.retrieval_log import markdown

    monkeypatch.setattr(
        markdown, "render", lambda payload: (_ for _ in ()).throw(TypeError("nope"))
    )
    with retlog.query_log("q", entrypoint="test"):
        with retlog.qdrant_call("vector_search", stage="dense_pull") as call:
            call.count_only(1)

    assert _only_trace(logging_on)["events"][0]["result_count"] == 1
    assert list(logging_on.rglob("report.md")) == []


def test_the_report_can_be_switched_off(logging_on, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "retrieval_log_report", False, raising=False)
    with retlog.query_log("q", entrypoint="test"):
        pass

    assert _traces(logging_on)
    assert list(logging_on.rglob("report.md")) == []


def test_the_folder_is_named_for_the_question_and_the_local_time():
    from datetime import datetime, timedelta, timezone

    ist = timezone(timedelta(hours=5, minutes=30), "IST")
    moment = datetime(2026, 8, 27, 10, 51, 10, tzinfo=ist)
    assert naming.folder_name("tell me about seagrass", moment) == (
        "tell me about seagrass - 2026-08-27 10-51-10 IST"
    )
    # A trailing "?" is illegal on Windows and distinguishes nothing.
    assert naming.folder_name("how many reports?", moment).startswith(
        "how many reports - "
    )


@pytest.mark.parametrize(
    "question, expected",
    [
        ('what about "blue carbon"?', 'what about _blue carbon_'),   # quotes
        ("energy: the 2024 report", "energy_ the 2024 report"),      # colon
        ("a/b vs c\\d", "a_b vs c_d"),                               # separators
        ("pipes | and * globs", "pipes _ and _ globs"),               # pipe, star
        ("line one\nline two", "line one line two"),                  # newline
        ("   padded   ", "padded"),
        ("", "(empty question)"),
        ("NUL", "_NUL"),                                    # a Windows device name
        ("trailing dots...", "trailing dots"),
    ],
)
def test_a_question_becomes_a_legal_path_component(question, expected):
    assert naming.slug(question) == expected


def test_a_long_question_is_truncated_but_stays_readable():
    name = naming.slug("carbon sequestration " * 20)
    assert len(name) <= naming.MAX_QUESTION_CHARS + 3
    assert name.startswith("carbon sequestration")
    assert name.endswith("...")


def test_two_identical_questions_in_one_second_get_their_own_folders(logging_on):
    """The name is for reading and promises nothing; `mkdir` enforces uniqueness."""
    for _ in range(3):
        with retlog.query_log("the same question", entrypoint="test"):
            pass

    traces = _traces(logging_on)
    assert len(traces) == 3
    names = sorted(p.parent.name for p in traces)
    assert names[0].startswith("the same question - ")
    # The later two are nudged rather than overwritten.
    assert any(n.endswith("(2)") for n in names)
    assert any(n.endswith("(3)") for n in names)
    ids = {json.loads(p.read_text(encoding="utf-8"))["request_id"] for p in traces}
    assert len(ids) == 3


def test_the_trace_records_both_clocks_and_its_own_folder(logging_on):
    with retlog.query_log("what about seagrass?", entrypoint="test") as log:
        folder = log.folder

    trace = _only_trace(logging_on)
    assert trace["folder"] == folder
    assert trace["timestamp"].endswith("+00:00")          # UTC inside the file
    assert "+05:30" in trace["timestamp_local"]            # IST for the layout
    digest = next(iter((logging_on / "summary").glob("*.jsonl")))
    row = json.loads(digest.read_text(encoding="utf-8").splitlines()[0])
    assert row["folder"].endswith(folder)                  # the digest points at it


def test_a_filter_tree_reads_as_one_line():
    """The shape conditions repeat on every pull; forty lines of tree per leg is
    what made a trace unreadable."""
    from qdrant_client.models import (
        DatetimeRange, FieldCondition, Filter, MatchAny, MatchText, MatchValue,
    )

    tree = Filter(
        must=[
            FieldCondition(key="is_parent", match=MatchValue(value=False)),
            FieldCondition(key="source_type", match=MatchValue(value="website")),
            FieldCondition(key="published_at", range=DatetimeRange(gte="2024-01-01")),
            Filter(should=[
                FieldCondition(key="chunk_text", match=MatchText(text="solar"))
            ]),
        ],
        must_not=[
            FieldCondition(key="section_type", match=MatchAny(any=["toc", "glossary"]))
        ],
    )
    line = views.filter_compact(safe.jsonable(tree))
    assert line == (
        "is_parent=false AND source_type=website "
        "AND published_at gte 2024-01-01T00:00:00 "
        "AND (ANY(chunk_text ~ 'solar')) AND NOT (section_type in [toc, glossary])"
    )


def test_a_bulk_vocabulary_load_is_counted_not_sampled(logging_on):
    """The read path loads whole gazetteers to resolve a question. The count and
    the SQL are the useful record; five of 8,507 author names are not."""
    with retlog.query_log("q", entrypoint="test"):
        with retlog.mysql_call("select", stage="catalog") as call:
            call.row_results([{"name": f"person {i}"} for i in range(views.BULK_ROWS + 1)])

    event = _only_trace(logging_on)["events"][0]
    assert event["result_count"] == views.BULK_ROWS + 1
    assert "results" not in event
    assert event["metrics"]["rows_sampled"] is False


def test_a_bulk_load_is_still_sampled_at_full_detail(full_detail):
    with retlog.query_log("q", entrypoint="test"):
        with retlog.mysql_call("select", stage="catalog") as call:
            call.row_results([{"name": f"person {i}"} for i in range(views.BULK_ROWS + 1)])

    event = _only_trace(full_detail)["events"][0]
    assert event["result_count"] == views.BULK_ROWS + 1
    assert len(event["results"]) == 3  # the fixture's max_results


def test_chunk_metadata_keeps_provenance_and_drops_the_rest():
    metadata = views.chunk_metadata(
        {
            "document_id": "d1",
            "title": "Annual Report",
            "page_number": 4,
            "chunk_text": "the body",     # carried as text, not as metadata
            "content_hash": "abc",        # ingestion bookkeeping
            "embedding_version": "v2",
        },
        limit=100,
    )
    assert metadata == {"document_id": "d1", "title": "Annual Report", "page_number": 4}


def test_log_root_defaults_beside_the_repository(monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "retrieval_log_dir", "", raising=False)
    root = sink.log_root()
    assert root.name == "logs"
    assert (root.parent / "app").is_dir()
