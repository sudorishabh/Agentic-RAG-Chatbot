"""Grade an N-run benchmark file and report the majority verdict per question.

Why majority
------------
The pipeline is not deterministic (see ``benchmark_chat.py``), so a single run's
verdict is a sample, not a measurement. This grades every run independently and
takes the per-question majority as the headline, while keeping the disagreement
visible: a question that answers twice and refuses once is a different thing
from one that answers three times, and collapsing them would hide exactly the
instability this harness exists to expose.

The verdict is automatic and therefore approximate
--------------------------------------------------
Grading 258 answers by hand is not practical, so the verdict is derived from
measurable signals:

* a refusal or meta-deflection, or an answer too short to be one  -> NO_ANSWER
* a list-shaped answer citing no gold document, with almost no fact
  coverage                                                        -> INCORRECT
* mean fact coverage at or above ``CORRECT_COVERAGE``             -> CORRECT
* anything else                                                   -> PARTIALLY_CORRECT

Calibrated against the 86 hand-assigned verdicts from the previous phase, this
rule agrees on **76 of 86 (88.4%)**. Every NO_ANSWER matched, and 3 of 4
INCORRECTs; the disagreements are all on the CORRECT/PARTIALLY_CORRECT boundary,
which is where a coverage threshold is inherently crude. Read the automatic
verdict as a stability instrument, not as a replacement for reading answers.

Fact coverage is measured exactly as in the earlier phases — the probe
extraction below is a copy of the one used for the baseline and fix runs — so
the numbers stay comparable across all three.

    python scripts/benchmark_grade.py --raw raw_3run.json --out results.json
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import statistics as st
import sys
from collections import Counter

DEFAULT_GOLD = os.path.join("reports", "benchmark", "organization_121_gold.json")

# Mean fact coverage at or above which an answer is called CORRECT, and the
# coverage below which a list-shaped answer citing nothing from the gold is
# called INCORRECT. Both fitted against the hand verdicts; see the module
# docstring for the agreement they achieve.
CORRECT_COVERAGE = 0.40
INCORRECT_COVERAGE = 0.14

# The shapes a refusal or a meta-deflection takes in this system.
_REFUSAL = re.compile(
    r"I don't have information|please ask me a more focused|"
    r"I can help (answer questions|you find)|I don't have specific information|"
    r"I can check for specific information", re.I)
_MIN_ANSWER_CHARS = 80
# How far into a response a refusal phrase still means the response *is* one.
_REFUSAL_LEAD = 120
_LIST_HEAD = "here is what i found"

_STOP = set("""the a an of to in on for and or with by from as at is are was were be been being this
that these those it its their our we us you your they them he she his her which who whom whose what
when where why how not no also more most other another such than then there here into over under
about across during within without between among per via both each any all some many few much less
least own same so too very can could may might must shall should will would do does did done have
has had having i ii iii states state including include includes included named name names use uses
used using work works working new news latest recent recently through covering covers cover across
level levels area areas based upon under first second third also states stated stating per cent""".split())


def probes(fact: str) -> list[tuple[str, str]]:
    """Distinctive strings that must appear in an answer if the fact is covered."""
    out: list[tuple[str, str]] = []
    for m in re.findall(r"['‘’\"“”]([^'‘’\"“”]{6,120})['‘’\"“”]", fact):
        out.append(("quote", m.strip()))
    for m in re.findall(r"\b\d[\d,\.]*\s?(?:%|GW|MT|kWth|MW|kg|tonnes)?\b", fact):
        m = m.strip()
        if len(m.replace(",", "").replace(".", "")) >= 2:
            out.append(("num", m))
    for m in re.findall(r"\b[A-Z]{2,}(?:-[A-Z0-9]+)*\b", fact):
        if m not in ("TERI", "AND", "THE"):
            out.append(("acro", m))
    for m in re.findall(
            r"\b(?:[A-Z][a-z’'&\-]+(?:\s+(?:of|for|and|the|on|in|to|de|la)\s+)?){2,}", fact):
        m = " ".join(m.split()).strip(" .,;:")
        if len(m) >= 10 and m.lower() not in ("the energy and resources institute",):
            out.append(("caps", m))
    for w in re.findall(r"\b[a-z][a-z\-]{6,}\b", fact.lower()):
        if w not in _STOP:
            out.append(("word", w))
    seen, uniq = set(), []
    for kind, value in out:
        if value.lower() in seen:
            continue
        seen.add(value.lower())
        uniq.append((kind, value))
    return uniq


def norm(s: str | None) -> str:
    s = (s or "").lower()
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-").replace("‑", "-")
    return re.sub(r"\s+", " ", s)


def _is_refusal(answer: str | None) -> bool:
    """Whether the response is a refusal, rather than merely containing one.

    A combined answer can be a real list followed by a refusal from the content
    half — measured on Q025, ten ongoing projects and their total, then "I don't
    have information on that in the available sources". Matching the phrase
    anywhere scored that as NO_ANSWER and threw away a substantive answer.
    Position is what separates the two shapes. A response that *is* a refusal
    opens with one; a response that merely ends with one has already answered.
    """
    text = (answer or "").strip()
    if len(text) < _MIN_ANSWER_CHARS:
        return True
    return bool(_REFUSAL.search(text[:_REFUSAL_LEAD]))


def _strip_markers(answer: str | None) -> str:
    return re.sub(r"</?\s*(website_answer|pdf_answer|db_answer|answer)\s*>", " ", answer or "")


def fact_coverage(fact: str, answer: str) -> float | None:
    """Share of a fact's distinctive probes present in the answer, or None."""
    found = probes(fact)
    if not found:
        return None
    strong = [(k, v) for k, v in found if k in ("quote", "num", "acro", "caps")]
    pool = strong or found
    return sum(1 for _, v in pool if norm(v) in answer) / len(pool)


def verdict_for(measures: dict) -> str:
    """The automatic verdict for one response. See the module docstring."""
    if measures["error"]:
        return "SYSTEM_ERROR"
    if measures["refused"]:
        return "NO_ANSWER"
    coverage = measures["mean_fact_coverage"] or 0.0
    if measures["list_shaped"] and not measures["cite_in_gold"] \
            and coverage < INCORRECT_COVERAGE:
        return "INCORRECT"
    if coverage >= CORRECT_COVERAGE:
        return "CORRECT"
    return "PARTIALLY_CORRECT"


def measure(record: dict, gold: dict) -> dict:
    """Everything gradeable about one response, before any verdict is assigned."""
    entry = gold[record["question_id"]]
    raw_answer = record["chat"]["answer"] or ""
    answer = norm(_strip_markers(raw_answer))
    sources = record["chat"].get("sources") or {}
    citations = sources.get("citations") or []
    cite_docs = [c.get("document_id") for c in citations if c.get("document_id")]
    gold_docs = set(entry["document_ids"])
    search = record.get("search") or {}
    blocks = search.get("blocks") or []
    block_docs = [b.get("document_id") for b in blocks if b.get("document_id")]

    scored = [c for c in (fact_coverage(f, answer) for f in entry["expected_facts"])
              if c is not None]
    return {
        "run": record["run"],
        "question_id": record["question_id"],
        "question": record["question"],
        "answer": raw_answer,
        "answer_chars": len(raw_answer),
        "error": record["chat"]["error"],
        "refused": _is_refusal(raw_answer),
        "list_shaped": norm(raw_answer).startswith(_LIST_HEAD),
        "intent": search.get("intent"),
        "answer_format": sources.get("answer_format"),
        "used_chunks": sources.get("used_chunks"),
        "n_blocks": search.get("n_blocks"),
        "n_citations": len(citations),
        "cite_in_gold": sorted(set(cite_docs) & gold_docs),
        "blocks_in_gold": sorted(set(block_docs) & gold_docs),
        "retrieved_titles": [b.get("title") for b in blocks],
        "gold_doc_count": len(gold_docs),
        "n_facts": len(entry["expected_facts"]),
        "facts_covered": sum(1 for c in scored if c >= 0.5),
        "mean_fact_coverage": round(st.mean(scored), 3) if scored else None,
        "latency_ms": record["chat"]["latency_ms"],
    }


def _material_change(answers: list[str]) -> bool:
    """Whether the answers differ in substance rather than in wording.

    Compared on the distinctive tokens each answer carries — numbers, acronyms
    and capitalised names — because two runs that name the same things have
    given the same answer however differently they phrased it.
    """
    signatures = []
    for answer in answers:
        tokens = set(re.findall(r"\b[A-Z]{2,}\b|\b\d[\d,\.]*\b", answer or ""))
        signatures.append(frozenset(tokens))
    if len(signatures) < 2:
        return False
    union = set().union(*signatures)
    if not union:
        return len({len((a or "").split()) > 20 for a in answers}) > 1
    common = set.intersection(*(set(s) for s in signatures))
    return len(common) / len(union) < 0.6


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--gold", default=DEFAULT_GOLD)
    ap.add_argument("--label", default="")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    gold = {q["question_id"]: q for q in json.load(
        io.open(args.gold, encoding="utf-8"))["questions"]}
    raw = json.load(io.open(args.raw, encoding="utf-8"))

    by_question: dict[str, list[dict]] = {}
    for record in raw:
        by_question.setdefault(record["question_id"], []).append(
            measure(record, gold))

    questions = []
    for qid in sorted(by_question):
        runs = sorted(by_question[qid], key=lambda m: m["run"])
        verdicts = [verdict_for(m) for m in runs]
        counts = Counter(verdicts)
        majority, agree = counts.most_common(1)[0]
        intents = [m["intent"] for m in runs]
        coverages = [m["mean_fact_coverage"] or 0.0 for m in runs]
        questions.append({
            "question_id": qid,
            "question": runs[0]["question"],
            "runs": [dict(m, verdict=v) for m, v in zip(runs, verdicts)],
            "verdicts": verdicts,
            "majority_verdict": majority,
            "majority_size": agree,
            "unanimous": len(counts) == 1,
            "disagreements": len(runs) - agree,
            "intent_flapped": len(set(intents)) > 1,
            "intents": intents,
            "answer_flapped": _material_change([m["answer"] for m in runs]),
            "coverage_spread": round(max(coverages) - min(coverages), 3),
            "mean_fact_coverage": round(st.mean(coverages), 3),
            "gold_doc_hit_runs": sum(1 for m in runs if m["blocks_in_gold"]),
            "gold_cite_hit_runs": sum(1 for m in runs if m["cite_in_gold"]),
            "mean_latency_ms": round(st.mean([m["latency_ms"] for m in runs]), 1),
        })

    n = len(questions)
    runs_per_question = Counter(len(q["runs"]) for q in questions)
    latencies = sorted(m["latency_ms"] for q in questions for m in q["runs"])

    def pct(p):
        return round(latencies[min(len(latencies) - 1, int(len(latencies) * p))], 1)

    verdict_counts = Counter(q["majority_verdict"] for q in questions)
    summary = {
        "label": args.label or os.path.basename(args.raw),
        "questions": n,
        "runs_per_question": dict(runs_per_question),
        "majority_verdicts": dict(verdict_counts),
        "strict_success_rate": round(verdict_counts.get("CORRECT", 0) / n, 4) if n else 0,
        "stability": {
            "unanimous_questions": sum(1 for q in questions if q["unanimous"]),
            "unstable_questions": sum(1 for q in questions if not q["unanimous"]),
            "unstable_ids": [q["question_id"] for q in questions if not q["unanimous"]],
            "intent_flapping": sum(1 for q in questions if q["intent_flapped"]),
            "intent_flapping_ids": [q["question_id"] for q in questions if q["intent_flapped"]],
            "answer_flapping": sum(1 for q in questions if q["answer_flapped"]),
            "answer_flapping_ids": [q["question_id"] for q in questions if q["answer_flapped"]],
            "mean_coverage_spread": round(
                st.mean([q["coverage_spread"] for q in questions]), 4) if n else 0,
        },
        "retrieval": {
            "gold_document_retrieval_rate_majority": round(sum(
                1 for q in questions if q["gold_doc_hit_runs"] * 2 > len(q["runs"])) / n, 4),
            "gold_citation_rate_majority": round(sum(
                1 for q in questions if q["gold_cite_hit_runs"] * 2 > len(q["runs"])) / n, 4),
            "mean_fact_coverage": round(
                st.mean([q["mean_fact_coverage"] for q in questions]), 4) if n else 0,
        },
        "latency_ms": {"p50": pct(0.50), "p90": pct(0.90), "p95": pct(0.95),
                       "mean": round(st.mean(latencies), 1) if latencies else 0},
        "verdict_rule": {
            "correct_coverage_threshold": CORRECT_COVERAGE,
            "incorrect_coverage_ceiling": INCORRECT_COVERAGE,
            "agreement_with_hand_verdicts": "76/86 (88.4%) on the previous phase's run",
        },
    }
    json.dump({"summary": summary, "questions": questions},
              io.open(args.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
