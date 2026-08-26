# Improving the Retrieval & Generation Flow

A plain-language look at how the system turns a question into an answer today,
and the concrete, low-risk ways we can make it better. Focused only on
**retrieval** (finding the evidence) and **generation** (writing the answer).

---

## Part 1 — How it works today

### Retrieval: from question to evidence

This is what happens inside `retrieve()` (`app/retrieval/retriever.py`), in order:

1. **Pick the base search.** Normally we search document chunks. If the
   "prefer website" feature is on and the user didn't pin a source, we do a
   **dual search** that also pulls website content.
2. **Optionally widen the net.** For plain question-answering with a longish
   query, we run **multi-query**: the question is rephrased a few ways and each
   rephrase is searched, so we don't miss results that use different wording.
3. **Optionally add a keyword leg.** Alongside the meaning-based (vector)
   search, we can run a plain **keyword** match for exact terms.
4. **Merge the lists (RRF).** The separate ranked lists are fused into one.
5. **Rerank.** A smarter model re-sorts the merged candidates by how well they
   actually answer the question (tables get a small boost when asked for).
6. **Correct if weak.** If the top result still looks poor (its score is below a
   threshold), we run **one** corrective retry with a reformulated query.
7. **Build the context.** Duplicates are removed and neighboring chunks are
   stitched together into clean evidence blocks.
8. **Supplement attachments.** For "detailed" answers, if a matched web page has
   an attached PDF that didn't make it in, we pull that PDF's chunks once.

The result is an ordered list of evidence blocks.

### Generation: from evidence to answer

This is the flow in `_prepare` + `stream_answer` (`app/pipeline/query_pipeline.py`):

1. **Understand the question.** We classify what the user wants (the multi-label
   "understanding") and rewrite the question to be standalone.
2. **Take a shortcut if we can.** Small talk, a pure database lookup, or a
   whole-corpus summary are answered directly without full retrieval.
3. **Check the cache.** If we've answered a very similar question before, reuse
   that answer.
4. **Retrieve** the evidence (Part 1 above).
5. **Refuse safely.** If nothing relevant was found, return a refusal instead of
   guessing.
6. **Write the answer.** The model streams the answer from the evidence blocks,
   shaped to the requested format (list, table, timeline, …).
7. **Check faithfulness.** After streaming, we verify the answer only uses the
   evidence. If it doesn't, we regenerate **once** and emit a correction.
8. **Flag stray numbers.** Numbers not found in the cited blocks are logged
   (observe-only for now — nothing is auto-changed).
9. **Save and record.** The final answer is cached and metrics are recorded.

---

## Part 2 — How we can improve it

Each item says **what**, **why**, and a rough **effort / risk**.

### Retrieval improvements

**R1. Run the database lookup and document search at the same time.**
Today, a "combined" question (needs both catalog facts and document content)
runs the database part first, then retrieval — one after the other. They don't
depend on each other, so they can run in parallel.
*Why:* lower latency, identical answers.
*Effort/risk:* small / low. **Best first step.**

**R2. Let "understanding" choose the search strategy — not word counts.**
Right now retrieval decides multi-query / keyword / dual from generic rules
(e.g. "5+ words"). But we already computed a rich understanding of the question
upstream (is it a comparison? a summary? scoped to one document?). Feed that in
so the choice is intentional — e.g. a comparison naturally wants multi-query.
*Why:* smarter strategy selection, fewer wasted searches.
*Effort/risk:* medium / medium.

**R3. Keep the corrective retry, but measure it.**
The one-shot corrective loop must stay inside retrieval — it reacts to a
*result* (a weak top score) that can't be predicted in advance. What we don't
know is whether it actually helps. Log when it fires and whether the answer
improved.
*Why:* decide with data before tuning or removing it.
*Effort/risk:* small / low.

**R4. Hide retrieval's knobs behind one clear entrance.**
Callers shouldn't need to know about dual search, fusion, reranking, or
attachment pulls. Keep those internal to the retrieval service and expose one
simple call.
*Why:* the rest of the system stays simple; internals can change freely.
*Effort/risk:* small / low (mostly a tidy-up).

### Generation improvements

**G1. Stream the deterministic database section first (already done) — keep it.**
For combined answers we already show the exact catalog facts before the written
part. Good pattern; just make sure the cache stores the composed result.
*Why:* users see reliable facts instantly.
*Effort/risk:* none / done — a check, not a change.

**G2. Decide what the numeric check should *do*.**
We currently only *log* numbers that aren't in the sources. Either promote it to
a visible warning on the answer, or leave it observe-only on purpose — but make
that a deliberate choice, not a leftover.
*Why:* stray numbers are exactly the errors users trust least.
*Effort/risk:* small / low.

**G3. Cache the corrected answer, not the first draft.**
When the faithfulness check triggers a one-time regeneration, make sure the
*corrected* version is the one cached (verify the current order).
*Why:* we shouldn't re-serve an answer we already judged unfaithful.
*Effort/risk:* small / low.

---

## Part 3 — Suggested order

Do the safe, high-value work first; leave anything that needs judgement for
after we have measurements.

1. **R1** — parallelize database + document search (quick latency win).
2. **G2, G3, R3** — small correctness/observability fixes; add measurement.
3. **R4** — tidy retrieval behind one entry point.
4. **R2** — drive strategy from understanding (do this once R4 makes it clean).

> Rule of thumb: don't delete or heavily tune a retrieval strategy
> (multi-query, corrective loop, keyword leg) until R3's measurements show
> whether it earns its keep. Some of these quietly improve accuracy.
