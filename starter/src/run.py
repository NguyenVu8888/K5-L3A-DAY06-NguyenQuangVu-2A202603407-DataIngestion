"""Main orchestration script for Day 06 Data Ingestion Engineering pipeline.

Runs Strategies A, B, and C on both dev and test splits, logs top-3 traces,
and outputs performance metrics.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

from .chunking import by_paragraph, fixed_size
from .embeddings import get_embedder
from .evaluation import evaluate_query, summarize
from .ingestion import load_pdf
from .store import QdrantVectorStore

# Load environment
load_dotenv()


def run_pipeline() -> dict[str, Any]:
    project_root = Path(__file__).resolve().parent.parent.parent
    pdf_path = project_root / "2023-BC-toan-canh-cong-nghe-AI-cham-soc-suc-khoe.pdf"
    benchmark_path = project_root / "benchmark" / "questions.json"
    results_dir = project_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    print("==================================================")
    print("DAY 06 · DATA INGESTION ENGINEERING PIPELINE")
    print("==================================================")

    # 1. Load corpus
    print("\n[Step 1/5] Loading and normalizing corpus...")
    pages = load_pdf(pdf_path, include_cover_and_toc=False)
    print(f"Loaded {len(pages)} content pages ({sum(len(p.text) for p in pages):,} characters).")

    # 2. Load benchmark questions
    print("\n[Step 2/5] Loading benchmark questions...")
    if not benchmark_path.exists():
        raise FileNotFoundError(f"Benchmark file not found at {benchmark_path}")
    questions: list[dict[str, Any]] = json.loads(benchmark_path.read_text(encoding="utf-8"))
    dev_q = [q for q in questions if q.get("split") == "dev"]
    test_q = [q for q in questions if q.get("split") == "test"]
    print(f"Loaded {len(questions)} questions (Dev: {len(dev_q)}, Test: {len(test_q)}).")

    # 3. Build chunking datasets
    print("\n[Step 3/5] Building chunk strategies...")
    # Strategy A: fixed-size
    chunks_a = []
    for p in pages:
        chunks_a.extend(fixed_size(p, size=500, overlap=50))
    print(f"  - Strategy A (Fixed-size 500/50): {len(chunks_a)} chunks")

    # Strategy B & C: paragraph-aware
    chunks_b = []
    for p in pages:
        chunks_b.extend(by_paragraph(p, max_size=800))
    print(f"  - Strategy B/C (Paragraph-aware max 800): {len(chunks_b)} chunks")

    # 4. Initialize Embedder and Vector Store
    print("\n[Step 4/5] Initializing Embedder and Vector Store...")
    embedder = get_embedder()
    print(f"  - Model: {embedder.model_name} ({embedder.dimensions} dimensions)")

    store_path = results_dir / "qdrant_data"
    store = QdrantVectorStore(storage_path=str(store_path), dimensions=embedder.dimensions)
    print(f"  - Vector Store: Qdrant Local Persistent at {store_path}")

    # Ingest Strategy A
    print("\nIngesting Strategy A...")
    t0 = time.time()
    texts_a = [c.text for c in chunks_a]
    vectors_a = embedder.embed_documents(texts_a)
    store.upsert("strategy_a", chunks_a, vectors_a)
    ingest_time_a = time.time() - t0
    print(f"  -> Ingested {len(chunks_a)} chunks into strategy_a in {ingest_time_a:.2f}s")

    # Ingest Strategy B (and C uses same index with metadata filter)
    print("\nIngesting Strategy B/C...")
    t0 = time.time()
    texts_b = [c.text for c in chunks_b]
    vectors_b = embedder.embed_documents(texts_b)
    store.upsert("strategy_b", chunks_b, vectors_b)
    ingest_time_b = time.time() - t0
    print(f"  -> Ingested {len(chunks_b)} chunks into strategy_b in {ingest_time_b:.2f}s")

    # 5. Execute Benchmark Searches across A, B, C
    print("\n[Step 5/5] Executing benchmark retrieval & trace generation...")
    all_traces: list[dict[str, Any]] = []

    strategies_config = [
        {"name": "Strategy_A", "col": "strategy_a", "use_filter": False},
        {"name": "Strategy_B", "col": "strategy_b", "use_filter": False},
        {"name": "Strategy_C", "col": "strategy_b", "use_filter": True},
    ]

    # Pre-embed questions to avoid duplicate API calls
    query_vectors = {}
    print("Embedding query questions...")
    for q in questions:
        query_vectors[q["id"]] = embedder.embed_query(q["question"])

    for cfg in strategies_config:
        strat_name = cfg["name"]
        col = cfg["col"]
        use_filter = cfg["use_filter"]
        print(f"  Running retrieval for {strat_name}...")

        for q in questions:
            q_vec = query_vectors[q["id"]]
            filters = q.get("filter") if use_filter else None
            hits = store.search(strategy=col, query_vector=q_vec, top_k=3, filters=filters)
            trace = evaluate_query(question=q, hits=hits, strategy=strat_name)
            all_traces.append(trace)

    # Save full traces
    traces_file = results_dir / "traces.json"
    traces_file.write_text(json.dumps(all_traces, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved {len(all_traces)} traces to {traces_file}")

    # Compute summary metrics
    summary = summarize(all_traces)
    summary_file = results_dir / "summary.json"
    summary_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n================== SUMMARY RESULTS ==================")
    for strat, splits in summary.items():
        print(f"\n--- {strat} ---")
        for split_name, metrics in splits.items():
            print(f"  [{split_name.upper()}] Hit@1: {metrics['hit_at_1_rate']} | Evidence Hit@3: {metrics['hit_at_3_rate']}")

    return {
        "summary": summary,
        "traces_file": str(traces_file),
        "ingest_time_a": ingest_time_a,
        "ingest_time_b": ingest_time_b,
        "chunks_a": len(chunks_a),
        "chunks_b": len(chunks_b),
        "embedder": embedder.model_name,
        "dimensions": embedder.dimensions,
    }


def main() -> None:
    run_pipeline()


if __name__ == "__main__":
    main()
