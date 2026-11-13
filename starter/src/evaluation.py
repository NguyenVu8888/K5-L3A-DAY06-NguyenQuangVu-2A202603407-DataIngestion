"""Evaluation functions for retrieval accuracy, Hit@1, Evidence Hit@3, and trace logging."""
from __future__ import annotations

import re
from typing import Any


def check_hit(hit: dict[str, Any], question: dict[str, Any]) -> tuple[bool, str]:
    """Check if a retrieved chunk matches gold page and contains enough gold evidence."""
    gold_page = question.get("gold_page")
    retrieved_page = hit.get("page")
    evidence_quote = question.get("evidence_quote", "")
    chunk_text = hit.get("text", "")

    # Page check
    if retrieved_page != gold_page:
        return False, f"Page mismatch: got {retrieved_page}, expected {gold_page}"

    # Evidence check
    # 1. Exact or normalized substring match
    ev_clean = " ".join(evidence_quote.split()).lower()
    ch_clean = " ".join(chunk_text.split()).lower()

    if ev_clean in ch_clean:
        return True, "Exact evidence quote found in chunk text"

    # 2. Token overlap check for long evidence split or boundary cuts
    ev_tokens = set(re.findall(r"\w+", ev_clean))
    ch_tokens = set(re.findall(r"\w+", ch_clean))
    if ev_tokens:
        overlap = len(ev_tokens & ch_tokens) / len(ev_tokens)
        if overlap >= 0.85:
            return True, f"High evidence token overlap ({overlap:.1%})"

    return False, "Evidence quote not sufficiently contained in chunk text"


def evaluate_query(
    question: dict[str, Any],
    hits: list[dict[str, Any]],
    strategy: str = "",
) -> dict[str, Any]:
    """Evaluate retrieval top-k hits for a single question and record trace."""
    evaluated_hits = []
    has_hit_at_1 = False
    has_hit_at_3 = False

    for rank, hit in enumerate(hits, start=1):
        is_hit, reason = check_hit(hit, question)
        evaluated_hit = {
            "rank": rank,
            "chunk_id": hit.get("chunk_id", ""),
            "score": hit.get("score", 0.0),
            "page": hit.get("page", 0),
            "text": hit.get("text", ""),
            "metadata": hit.get("metadata", {}),
            "is_gold_page": hit.get("page") == question.get("gold_page"),
            "is_hit": is_hit,
            "reason": reason,
        }
        evaluated_hits.append(evaluated_hit)

        if rank == 1 and is_hit:
            has_hit_at_1 = True
        if rank <= 3 and is_hit:
            has_hit_at_3 = True

    trace = {
        "question_id": question.get("id"),
        "split": question.get("split"),
        "strategy": strategy,
        "question_type": question.get("question_type"),
        "question": question.get("question"),
        "expected_answer": question.get("expected_answer"),
        "gold_page": question.get("gold_page"),
        "filter": question.get("filter"),
        "evidence_quote": question.get("evidence_quote"),
        "hit_at_1": has_hit_at_1,
        "hit_at_3": has_hit_at_3,
        "top_3_hits": evaluated_hits[:3],
    }
    return trace


def summarize(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate Hit@1 and Evidence Hit@3 by strategy and split."""
    summary: dict[str, Any] = {}

    # Group by strategy and split
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for t in traces:
        key = (t.get("strategy", "unknown"), t.get("split", "all"))
        groups.setdefault(key, []).append(t)

    for (strat, split), group in groups.items():
        total = len(group)
        hit_1 = sum(1 for t in group if t.get("hit_at_1"))
        hit_3 = sum(1 for t in group if t.get("hit_at_3"))

        strat_summary = summary.setdefault(strat, {})
        strat_summary[split] = {
            "total_questions": total,
            "hit_at_1_count": hit_1,
            "hit_at_1_rate": f"{hit_1}/{total} ({hit_1/total:.1%})" if total else "0/0",
            "hit_at_3_count": hit_3,
            "hit_at_3_rate": f"{hit_3}/{total} ({hit_3/total:.1%})" if total else "0/0",
        }

    return summary
