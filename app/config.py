from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2024-06-01"
    azure_openai_model: str = ""
    llm_structured_temperature: float | None = None
    azure_openai_embedding_model: str = ""
    azure_openai_embedding_key: str = ""
    azure_openai_embedding_endpoint: str = ""
    azure_openai_embedding_api_version: str = "2024-06-01"
    # Output vector size for the embedding model. text-embedding-3-{small,large}
    # support Matryoshka truncation to a smaller dimension; 1536 halves storage
    # and search cost vs 3-large's native 3072 with negligible retrieval loss.
    # Set to None (leave blank) for ada-002, which does not accept this param.
    azure_openai_embedding_dimensions: int | None = 3072
    # Retries the OpenAI SDK spends on one embedding call before it raises. It
    # retries 429 with exponential backoff, honouring Azure's `retry-after`, so
    # this is the whole defence against provisioned-throughput throttling — the
    # library's own `retry_min_seconds`/`retry_max_seconds` are declared but
    # never read. The SDK default of 2 is short of the "retry after 3 seconds"
    # Azure asks for under sustained load; 8 rides out a throttling window
    # instead of losing the document to `documents_retry`.
    azure_openai_embedding_max_retries: int = 8
    # Ceiling on one throttle pause, and the fallback when a 429 arrives without
    # a usable `retry-after`. Caps the damage a wrong or hostile header can do:
    # every embedding thread waits on this, so an unclamped value would stall
    # the whole run rather than one request.
    azure_openai_embedding_max_throttle_seconds: float = 60.0
    azure_document_intelligence_endpoint: str = ""
    azure_document_intelligence_key: str = ""
    # "prebuilt-read" is the OCR-only (basic) model: cheap, text only, no table
    # structure. "prebuilt-layout" costs ~6x more but also reconstructs tables
    # and document structure (and supports Markdown output).
    azure_document_intelligence_model: str = "prebuilt-read"
    pdf_scanned_char_threshold: int = 100
    # PDF extraction routing (app/ingestion/extractors): "hybrid" classifies each
    # page and routes per page — scanned/image pages to Azure OCR, born-digital
    # table pages to Camelot, the rest to PyMuPDF text; "azure_only" always uses
    # Azure OCR; "local_only" uses PyMuPDF text only.
    extraction_mode: str = "hybrid"
    # Camelot table extraction (born-digital table pages). "lattice" reads ruled
    # tables and needs Ghostscript; the extractor falls back to "stream" when
    # lattice finds nothing on a page.
    camelot_flavor: str = "lattice"
    # Per-page table detection (PyMuPDF). find_tables() is the primary, reliable
    # signal — it handles both ruled and borderless tables. The two extra
    # heuristics below are OFF by default: on heavily-designed PDFs (banners,
    # side panels, page borders, multi-column text) they fire on nearly every
    # page and over-route everything to Azure. Enable them only for simpler
    # corpora where biasing harder toward Azure is worth the false positives.
    pdf_detect_ruled_grid: bool = False
    pdf_table_min_grid_lines: int = 3
    pdf_detect_borderless_tables: bool = False
    pdf_borderless_min_aligned_rows: int = 4
    pdf_borderless_min_columns: int = 3
    # A text line repeated on >= this fraction of a document's pages is treated as
    # a running header/footer and stripped from every page (0 disables).
    pdf_running_header_min_fraction: float = 0.5
    # Drop chart/axis "number soup" lines (e.g. "2020 2030 2040 2050") — bare
    # numeric runs from figures that carry no semantic signal.
    pdf_drop_number_soup: bool = True
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "documents"
    redis_url: str = ""
    semantic_cache_enabled: bool = True
    # 0.995: near-verbatim rephrasings only. At the old 0.97 a subtly different
    # question (another year, another theme) could return the wrong cached
    # answer; correctness beats hit rate here. Lookups additionally require the
    # stored facet fingerprint to match.
    semantic_cache_threshold: float = 0.995
    # Semantic cache is backed by a dedicated Qdrant collection: a nearest-neighbor
    # lookup on the query embedding, gated by semantic_cache_threshold (cosine).
    semantic_cache_collection: str = "semantic_cache"
    # Cached-answer lifetime in seconds (stored as expires_at; Qdrant has no TTL).
    semantic_cache_ttl: int = 86400
    # Qdrant has no native TTL, so each entry stores an expires_at that lookups
    # filter out once stale; expired points are deleted every N stores (0 disables
    # the opportunistic prune — rely on lookup-time filtering / a scheduled prune).
    semantic_cache_prune_every: int = 200
    worker_sweep_interval_seconds: int = 3600
    worker_sweep_reconcile: bool = False
    # Cross-store reconciliation (app.ingestion.reconcile) after each sweep:
    # MySQL against Qdrant against the graph, logged and kept for /metrics. It
    # scrolls the whole collection, so it costs one pass over the points per
    # sweep — the price of not discovering silent drift months later. It only
    # ever reads, and never fails a sweep.
    verify_corpus_after_sweep: bool = True
    retrieval_top_k: int = 6
    retrieval_candidate_k: int = 40
    # Website-content preference (see docs/website-preference-retrieval.md).
    # When enabled, retrieval runs two pulls — website (source_type == "website")
    # and "not website" — merges them, and the context builder leads with a
    # concise website section (capped) followed by PDF depth. Enabled by default;
    # validate on representative queries before relying on it in production.
    prefer_website_enabled: bool = True
    # Website-only candidates pulled alongside the (larger) not-website pull.
    website_candidate_k: int = 20
    # Max website blocks admitted (the concise lead). PDFs then follow under
    # their own budget (see pdf_max_slots). Users' website needs are typically
    # met in ~2.
    website_max_slots: int = 2
    # Per-chunk raw-semantic relevance floor a website chunk must clear to take a
    # website slot (prevents padding the answer with weak website text). Scale is
    # reranker-provider specific (dense cosine here); tuned empirically in eval.
    website_chunk_floor: float = 0.30
    # PDF budget after the website lead (segregated/dual retrieval only). The top
    # pdf_max_slots PDF chunks are admitted unconditionally; one extra ("3rd")
    # slot opens only for a candidate whose raw semantic_score clears the
    # high-confidence bar below, and nothing past that slot is ever admitted.
    # Scale matches website_chunk_floor (raw semantic_score); tune in eval.
    pdf_max_slots: int = 2
    pdf_high_confidence_floor: float = 0.5
    hybrid_use_sparse: bool = False
    # Multi-query recall expansion: LLM paraphrases of the search query are
    # searched in parallel and RRF-fused with the base pull. Gated per query
    # (qa intent, no explicit filters, non-trivial length). Launches OFF; flip
    # after eval.
    multi_query_enabled: bool = False
    multi_query_paraphrases: int = 2
    # Self-consistency routing: number of concurrent query-analysis samples,
    # majority-voted per field. 1 = single pinned-temperature call (today's
    # behavior); >1 samples at exploratory temperature. Flip to 3 only after
    # the routing eval shows a win.
    analysis_votes: int = 1
    # Minimum per-label confidence for a multi-label intent to be kept: the
    # agreement share across samples when analysis_votes > 1, else the model's
    # self-reported score. Terminal intents (chitchat/out_of_scope/…) are gated
    # by the same bar.
    intent_confidence_threshold: float = 0.5
    # One-shot corrective retrieval: when the reranked top candidate's raw
    # semantic score is below corrective_min_score, reformulate the query once,
    # search again, RRF-fuse and rerank. Strictly one iteration. Launches OFF;
    # eval must show a recall win within the latency budget before flipping.
    corrective_loop_enabled: bool = False
    corrective_min_score: float = 0.2
    # Keyword leg over the chunk_text full-text index (created by
    # scripts/create_fulltext_index.py): salient query terms drive one extra
    # MatchText-filtered pull fused with the dense pull via RRF. Fails open to
    # dense-only while the index is absent. Launches OFF. (hybrid_use_sparse
    # stays reserved for true sparse vectors, which need ingest-time writes.)
    keyword_leg_enabled: bool = False
    # Database Planner v2: use an LLM to decompose a catalog (database-intent)
    # question into one or more tool calls (comparisons like "2023 vs 2024", a
    # count paired with a list). OFF uses the deterministic single-call v1 plan;
    # any planner failure falls back to v1 as well. Launches OFF; flip after eval.
    database_multi_call_enabled: bool = False
    # Fuzzy entity resolution (app.retrieval.structured.resolve): scores a
    # free-text name against known authors/bundles/themes. OFF means an
    # unresolved theme/tag filter falls through to semantic search exactly as
    # before (today's behavior); ON makes it a terminal, explicit answer
    # ("no theme matching 'X' found") instead, and lets the v2 planner
    # advertise resolve_entity as a callable tool. This is the one switch for
    # the whole feature's change in fall-through behavior. Launches OFF; flip
    # after eval.
    entity_resolution_enabled: bool = False
    reranker_provider: str = "embedding"
    rerank_model: str = ""
    rerank_score_threshold: float = 0.0
    # How far apart two candidates' relevance scores may sit and still count as
    # "similarly relevant" — the width of a ranking band. Inside a band the newer
    # document leads; across bands relevance always wins, however old the winner
    # is. Sized for the 0..1 scale the embedding, llm and cohere providers return;
    # raise it for cross_encoder, whose scores are unbounded logits. Widen to let
    # recency decide more often, narrow to make it decide less.
    rerank_relevance_tolerance: float = 0.03
    # Multiplier on that tolerance when the query is about something that goes
    # out of date — pricing, an API, a regulation, an announcement (see
    # app.retrieval.volatility). A wider band lets the recency tie-break fire
    # more often; it never lets recency cross a band, so relevance still decides.
    # Set to 1.0 to rank volatile and stable topics identically.
    rerank_volatile_tolerance_multiplier: float = 2.0
    # How much more text one passage must hold than another before it counts as
    # "substantially more complete" and leads it — the completeness tier, which
    # sits below relevance and above recency. Length is a proxy: accuracy is not
    # measurable at ranking time, but a chunk cut short carries less of an answer
    # than a full one. Raise it to make completeness matter less; a very large
    # value hands every relevance tie to recency.
    rerank_substance_ratio: float = 1.5
    # Additive boost to a candidate's blended score when it contains a table and
    # the user asked for a table-shaped answer. Soft (not a filter) so a table
    # request still returns non-table results when no table matches.
    rerank_table_boost: float = 0.15
    dedup_cosine_threshold: float = 0.92
    # Max tokens of retrieved context sent to the LLM. Blocks are parent chunks
    # (~1800 tokens each), so this gates roughly context_token_budget / 1800
    # passages; 9000 keeps ~5 diverse sources — sized so the website-preference
    # split (2 website + ~3 PDF depth) can fit. Prefill cost/latency rises only on
    # content-rich queries (see docs/website-preference-retrieval.md §9, §13).
    context_token_budget: int = 9000
    faithfulness_check: bool = False
    metrics_log_enabled: bool = True
    # Max chat generations driven concurrently on the dedicated chat capacity
    # limiter. The /chat pipeline is blocking (LLM + Qdrant + Redis clients),
    # so each active stream occupies a worker thread for most of its life;
    # giving chat its own limiter keeps those long generations from starving
    # the shared request threadpool (~40 threads) that auth dependencies,
    # probes and other sync offloads borrow from. Extra chats queue here.
    chat_stream_max_concurrency: int = 64
    # Expose infrastructure detail (collection name, point counts, tuning
    # values, raw error strings) on /ready and /metrics. Off by default: the
    # retrieval API is public-facing and those bodies fingerprint the
    # deployment — probes only need the status codes. Enable on private /
    # dev deployments for human debugging.
    ops_detail_enabled: bool = False
    # JWT group whose members may read /metrics and /metrics/timings even when
    # ops_detail_enabled is off (e.g. "admin"). Only honored when auth_enabled —
    # without verified tokens every caller is anonymous and a group grant would
    # be meaningless. Empty (default) disables the group grant entirely.
    ops_admin_group: str = ""
    cors_allow_origins: str = "*"
    # Authentication for the public retrieval API (/chat, /search). When enabled,
    # requests must carry a Bearer JWT that the backend verifies; user_groups
    # are taken from the token's claims, never from the request body. Groups do
    # not scope retrieval (the corpus is public) — they only widen access to the
    # ops endpoints. Off by default (anonymous caller = groups ["public"]).
    auth_enabled: bool = False
    # Key used to verify the JWT signature. For HS* algorithms this is the shared
    # secret; for RS*/ES* it is the PEM-encoded public key.
    jwt_secret: str = ""
    # Comma-separated allow-list of accepted signing algorithms. Anything outside
    # this list (including the unsigned "none" algorithm) is rejected.
    jwt_algorithms: str = "HS256"
    # Optional audience / issuer to enforce when set (empty = not checked).
    jwt_audience: str = ""
    jwt_issuer: str = ""
    # Claim name carrying the caller's authorization groups.
    jwt_groups_claim: str = "groups"
    # Authentication for the ingestion control plane (/ingest/*, /reindex),
    # verified with the same JWT machinery as the retrieval API. Deliberately a
    # separate switch from `auth_enabled`, and deliberately ON: these routes
    # crawl the corpus, inject documents into the answer set, queue rebuilds and
    # read back internal ids and error strings. A deployment that has not enabled
    # retrieval auth is precisely the one that would otherwise leave them open.
    # Turn this off only for an ingestion server on a private interface whose
    # operators accept that anyone who can reach it may drive it.
    ingest_auth_enabled: bool = True
    # JWT group required for the *mutating* ingestion routes (crawl, article
    # injection, reindex). Falls back to `ops_admin_group`; when neither is set
    # the group check cannot mean anything, so any authenticated caller may
    # proceed and the gap is logged. Reading the ingest log needs authentication
    # but no group.
    ingest_admin_group: str = ""
    otel_enabled: bool = False
    otel_service_name: str = "agentic-rag"
    otel_exporter_otlp_endpoint: str = ""
    # Neo4j backs the knowledge graph (canonical entities, aliases, claims,
    # provenance). It is a rebuildable projection of MySQL + Qdrant, never a
    # system of record, so an outage degrades the knowledge layer and loses
    # nothing. Community edition offers no role-based access control, so the
    # read-only boundary for retrieval is enforced in code (see
    # app/core/clients/graph.py) rather than by a restricted database user.
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    # Community supports exactly one user database, named "neo4j".
    neo4j_database: str = "neo4j"
    neo4j_connection_timeout: float = 10.0
    # Master switch for the knowledge layer (entity/claim extraction, graph
    # projection). OFF: with this false nothing in the app opens a Neo4j
    # connection and ingestion/retrieval behave exactly as they do today.
    # Per-stage flags arrive with the stages they gate.
    knowledge_enabled: bool = False
    # Refresh the graph projection at the end of each sweep, so it stops drifting
    # the moment nobody remembers to run scripts.project_graph. Gated by
    # knowledge_enabled, so it is inert on a deployment without a graph, and
    # fail-open in every direction: an unreachable Neo4j costs a log line and
    # never touches the ingestion that already succeeded.
    graph_project_after_sweep: bool = True
    # How old a projection may be before reconciliation calls it stale. Sized
    # well above the sweep interval so an ordinary missed run is not an alarm;
    # what it catches is projection having stopped happening at all.
    graph_projection_max_age_seconds: int = 86400
    # Graph-backed retrieval. Separate from knowledge_enabled because the graph
    # must be built and verified long before any query is allowed to read it.
    graph_retrieval_enabled: bool = False
    # THE KILL SWITCH for graph routing. With this false no query is answered
    # from the graph, whatever the class list below says, and the graph package
    # is not imported on the request path. Flipping it back to false is the
    # complete rollback -- nothing else has to be undone, because existing
    # retrieval was never replaced, only bypassed for classes with evidence.
    #
    # ON as of Phase 11, for the four measured classes only. The evidence:
    # answer coverage 0.00 -> 1.00 against existing retrieval on those classes,
    # routing precision 1.00 (no false routes on the 24-query benchmark),
    # citation validity 1.00, and latency roughly halved. Every other class,
    # `historical` included, still falls through to existing retrieval.
    graph_routing_enabled: bool = True
    # Query classes routing may use, comma-separated. Empty means the built-in
    # default (see app.retrieval.graph.policy.DEFAULT_ENABLED_CLASSES).
    # `historical` is intentionally not in that default: it stays in shadow
    # until a larger reviewed historical benchmark exists.
    graph_routing_classes: str | None = None
    # Wall-clock budget for a whole graph attempt. Exceeding it falls back to
    # existing retrieval; measured p95 is far below this.
    graph_routing_budget_seconds: float = 3.0
    # Shadow mode: run graph retrieval beside production and log the comparison,
    # without touching the answer. Separate from graph_retrieval_enabled because
    # the point is to gather evidence on live traffic *before* routing anything.
    # The observation runs on a background thread and returns nothing, so with
    # this on the user's answer is still exactly what production produced.
    graph_shadow_enabled: bool = False
    # Optional JSONL destination for shadow observations. Unset: they go to the
    # application log only.
    graph_shadow_log_path: str | None = None
    # LLM claim extraction. The single most expensive step in the knowledge
    # layer -- one model call per eligible chunk -- so it is gated separately
    # from knowledge_enabled and launches OFF. The deterministic CMS-field
    # extractor needs no flag: it costs nothing and calls no model.
    claim_extraction_enabled: bool = False
    # A claim below this confidence is rejected rather than staged. CMS-field
    # claims assert 1.0, so this only ever bites model-proposed ones.
    claim_min_confidence: float = 0.6
    # Ceiling on model calls in one claim-extraction run, so an accidental
    # full-corpus pass cannot spend without bound. 0 disables the extractor.
    claim_llm_max_calls_per_run: int = 200
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = ""
    mysql_password: str = ""
    mysql_database: str = ""
    mysql_connect_timeout: int = 10
    mysql_pool_size: int = 5
    # Max seconds a caller waits for a free pooled connection before failing fast
    # (instead of blocking forever) when every connection is checked out.
    mysql_pool_timeout: int = 30
    drupal_jsonapi_base: str = "https://teriin.org/jsonapi"
    drupal_request_timeout: int = 60
    drupal_page_size: int = 50
    drupal_max_retries: int = 3
    # When true, PDF links in rich text that point to external (non-teriin.org)
    # domains are also downloaded and extracted. Off by default: the corpus
    # stays TERI-authored and the external URL still survives in the body text.
    drupal_ingest_external_pdfs: bool = False
    # Custom blocks (block_content) shorter than this (stripped body) are treated
    # as chrome/boilerplate (Search box, "Follow us" strip) and skipped — unless
    # they carry a harvestable PDF link.
    drupal_block_min_chars: int = 200
    # Evidence-based publication-date resolution for attached PDFs
    # (app.ingestion.date_resolution). With this off, every PDF simply inherits
    # its node's date, which is the behaviour that predates the resolver. With it
    # on, a PDF may carry its own date only when the document states one and every
    # validated gate passes; the decision and its evidence are recorded in
    # `{state}_date_decision` either way.
    date_resolution_enabled: bool = True
    ingest_state_table: str = "documents"
    # Append-only audit log of every ingestion event (one row per file/record
    # per run), separate from the overwrite-in-place documents table.
    ingest_log_table: str = "ingest_log"
    ingest_log_enabled: bool = True
    # Whether to record a per-document row for UNCHANGED docs. Off by default:
    # on an incremental sweep almost every doc is unchanged, so logging each one
    # is write amplification (one INSERT+commit per doc) and the main driver of
    # the log's growth. The run-level tally already reports the unchanged count.
    ingest_log_unchanged: bool = False
    # Days to keep ingest-log rows; older rows are pruned after each background
    # sweep. 0 disables pruning (the log then grows without bound).
    ingest_log_retention_days: int = 90
    # Batch controls for large (re)ingests. max_docs_per_run caps how many
    # documents actually get processed per run (new/changed/deleted; unchanged
    # scans are free) before the run stops cleanly; 0 = unlimited. Drupal
    # bundles are always crawled oldest-first, so the changed high-water mark
    # doubles as a resume cursor — a capped or interrupted run continues where
    # it stopped. batch_size/pause throttle within a run: sleep pause seconds
    # after every batch_size processed documents. workers > 1 processes that
    # many documents concurrently (one crawler, a pool of document workers —
    # keep workers below mysql_pool_size); the one-run-at-a-time lock still
    # applies.
    # Ingest-time LLM enrichment (app/ingestion/enrich.py): a per-document
    # abstract, generated once per content hash and cached in the
    # `<state>_enrichment` table. Launches OFF — the first pass over an existing
    # corpus costs real money, so it should be a deliberate act (flip this, or
    # run the backfill CLI) rather than something a scheduled sweep discovers.
    # With it on, the sweep enriches documents as it re-crawls them; documents
    # that never change are the backfill's job.
    enrichment_enabled: bool = False
    # How many times one document may fail enrichment before the sweep stops
    # retrying it. A version change (new prompt or model) resets the budget.
    enrichment_max_attempts: int = 3
    ingest_max_docs_per_run: int = 0
    ingest_batch_size: int = 0
    ingest_batch_pause_seconds: float = 0.0
    ingest_workers: int = 1
    # Delete reconciliation infers deletion from absence, so a live enumeration
    # that merely came back short is indistinguishable from a bundle that was
    # really emptied — and the deletion is immediate and total (points, catalog
    # row, facet rows) with nothing to restore from. HTTP failures already skip
    # the bundle; these two bound the damage a *successful* short response can do.
    #
    # A bundle is left alone when the share of its catalogued documents missing
    # from the live set reaches this fraction: 0.10 means one run may never
    # remove a tenth of a bundle.
    ingest_reconcile_max_missing_ratio: float = 0.10
    # ...except for this many documents, so a genuinely small bundle can still
    # lose one. Kept far below `drupal_page_size`, since the failure being
    # guarded against loses whole pages — an allowance this small cannot hide it.
    ingest_reconcile_min_deletions: int = 2


@lru_cache
def get_settings() -> Settings:
    return Settings()
