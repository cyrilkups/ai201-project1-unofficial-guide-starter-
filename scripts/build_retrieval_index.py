#!/usr/bin/env python3
"""Build and test the Milestone 4 retrieval layer."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer


ROOT = Path(__file__).resolve().parent.parent
CHUNKS_PATH = ROOT / "artifacts" / "chunks.jsonl"
CHROMA_DIR = ROOT / "chroma_db"
ARTIFACTS_DIR = ROOT / "artifacts"
RETRIEVAL_EVAL_JSON = ARTIFACTS_DIR / "retrieval_eval.json"
RETRIEVAL_EVAL_TXT = ARTIFACTS_DIR / "retrieval_eval.txt"

COLLECTION_NAME = "omscs_unofficial_guide"
MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_TOP_K = 4
EMBED_BATCH_SIZE = 64

COURSE_METADATA = {
    "3": {"course_code": "CS-6515", "course_name": "Introduction to Graduate Algorithms"},
    "4": {"course_code": "CS-6515", "course_name": "Introduction to Graduate Algorithms"},
    "5": {"course_code": "CS-7641", "course_name": "Machine Learning"},
    "6": {"course_code": "CS-7641", "course_name": "Machine Learning"},
    "7": {"course_code": "CS-6300", "course_name": "Software Development Process"},
    "8": {"course_code": "CS-6300", "course_name": "Software Development Process"},
    "9": {"course_code": "CS-6310", "course_name": "Software Architecture and Design"},
    "10": {"course_code": "CS-6310", "course_name": "Software Architecture and Design"},
    "11": {"course_code": "CS-6603", "course_name": "AI, Ethics, and Society"},
    "12": {"course_code": "CS-6603", "course_name": "AI, Ethics, and Society"},
}

EVALUATION_QUERIES = [
    "What background does CS 6515 expect before a student takes it?",
    "What do students say makes CS 7641 Machine Learning difficult in practice?",
    "Is CS 6300 Software Development Process a good first OMSCS course?",
    "What risk shows up repeatedly in student feedback for CS 6310 Software Architecture and Design?",
    "How is CS 6603 AI, Ethics, and Society positioned compared with the other courses in this set?",
]


def load_chunks() -> list[dict[str, Any]]:
    with CHUNKS_PATH.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def build_metadata(chunk: dict[str, Any]) -> dict[str, Any]:
    course_meta = COURSE_METADATA.get(str(chunk["source_id"]), {})
    return {
        "chunk_id": chunk["chunk_id"],
        "source_id": chunk["source_id"],
        "source_slug": chunk["source_slug"],
        "source_title": chunk["source_title"],
        "source_type": chunk["source_type"],
        "focus": chunk["focus"],
        "url": chunk["url"],
        "block_index": int(chunk["block_index"]),
        "character_count": int(chunk["character_count"]),
        "course_code": course_meta.get("course_code", "GENERAL"),
        "course_name": course_meta.get("course_name", chunk["source_title"]),
    }


def embedding_text(chunk: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"Source: {chunk['source_title']}",
            f"Type: {chunk['source_type']}",
            f"Focus: {chunk['focus']}",
            chunk["text"],
        ]
    )


def chunk_batches(items: list[Any], size: int) -> list[list[Any]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def get_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME, local_files_only=True)


def get_client() -> chromadb.PersistentClient:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def rebuild_collection(model: SentenceTransformer, top_k: int = DEFAULT_TOP_K) -> int:
    chunks = load_chunks()
    client = get_client()

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine", "model_name": MODEL_NAME, "default_top_k": top_k},
    )

    ids = [chunk["chunk_id"] for chunk in chunks]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [build_metadata(chunk) for chunk in chunks]
    texts_for_embedding = [embedding_text(chunk) for chunk in chunks]

    for id_batch, doc_batch, meta_batch, text_batch in zip(
        chunk_batches(ids, EMBED_BATCH_SIZE),
        chunk_batches(documents, EMBED_BATCH_SIZE),
        chunk_batches(metadatas, EMBED_BATCH_SIZE),
        chunk_batches(texts_for_embedding, EMBED_BATCH_SIZE),
    ):
        embeddings = model.encode(
            text_batch,
            batch_size=min(EMBED_BATCH_SIZE, len(text_batch)),
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()
        collection.add(ids=id_batch, documents=doc_batch, metadatas=meta_batch, embeddings=embeddings)

    return collection.count()


def get_collection() -> chromadb.Collection:
    client = get_client()
    return client.get_collection(COLLECTION_NAME)


def course_code_from_query(query: str) -> str | None:
    match = re.search(r"\bCS[- ]?(\d{4})\b", query, flags=re.IGNORECASE)
    if not match:
        return None
    return f"CS-{match.group(1)}"


def expand_query(query: str) -> str:
    lower = query.lower()
    additions: list[str] = []

    if any(token in lower for token in ["background", "prereq", "expect before", "before a student takes"]):
        additions.append(
            "background knowledge undergraduate preparation foundational algorithms "
            "discrete math graph algorithms dynamic programming divide and conquer"
        )

    if any(token in lower for token in ["difficult", "difficulty", "in practice", "workload"]):
        additions.append("workload projects assignments time commitment math heavy open ended")

    if any(token in lower for token in ["first omscs course", "first course", "beginning of the program"]):
        additions.append("good first course beginning of the program beginner friendly introductory")

    if not additions:
        return query

    return f"{query}\n" + "\n".join(additions)


def normalize_token(token: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "", token.lower())
    if len(token) > 5 and token.endswith("ing"):
        token = token[:-3]
    elif len(token) > 4 and token.endswith("ed"):
        token = token[:-2]
    elif len(token) > 3 and token.endswith("s"):
        token = token[:-1]
    return token


def overlap_tokens(text: str) -> set[str]:
    stopwords = {
        "a",
        "about",
        "an",
        "and",
        "are",
        "as",
        "at",
        "before",
        "do",
        "does",
        "for",
        "how",
        "in",
        "is",
        "it",
        "of",
        "on",
        "say",
        "student",
        "students",
        "the",
        "to",
        "what",
    }
    tokens = {
        normalize_token(token)
        for token in re.findall(r"[A-Za-z0-9-]+", text)
    }
    return {token for token in tokens if token and token not in stopwords and len(token) > 1}


def query_prefers_official_page(query: str) -> bool:
    lower = query.lower()
    return any(word in lower for word in ["background", "prereq", "expect", "before a student takes"])


def query_prefers_student_reviews(query: str) -> bool:
    lower = query.lower()
    return any(
        phrase in lower
        for phrase in [
            "students say",
            "student feedback",
            "in practice",
            "good first omscs course",
            "good first course",
            "risk shows up",
            "feedback for",
        ]
    )


def retrieve(query: str, model: SentenceTransformer, top_k: int = DEFAULT_TOP_K) -> list[dict[str, Any]]:
    collection = get_collection()
    embedded_query = expand_query(query)
    query_embedding = model.encode(
        [embedded_query],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    ).tolist()
    course_code = course_code_from_query(query)
    prefers_official = query_prefers_official_page(query)
    prefers_reviews = query_prefers_student_reviews(query)
    if course_code and prefers_official:
        where_filter = {"$and": [{"course_code": course_code}, {"source_type": "official page"}]}
    elif course_code and prefers_reviews:
        where_filter = {"$and": [{"course_code": course_code}, {"source_type": "student review page"}]}
    elif course_code:
        where_filter = {"course_code": course_code}
    else:
        where_filter = None
    candidate_count = max(top_k * 4, 12)
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=candidate_count,
        include=["documents", "metadatas", "distances"],
        where=where_filter,
    )

    matches: list[dict[str, Any]] = []
    q_tokens = overlap_tokens(query)
    for index in range(len(results["ids"][0])):
        metadata = results["metadatas"][0][index]
        text = results["documents"][0][index]
        chunk_tokens = overlap_tokens(f"{metadata['source_title']} {text}")
        overlap_ratio = len(q_tokens & chunk_tokens) / max(len(q_tokens), 1)
        adjusted_distance = float(results["distances"][0][index]) - (0.18 * overlap_ratio)
        if prefers_official and metadata["source_type"] == "official page":
            adjusted_distance -= 0.08
        matches.append(
            {
                "rank": index + 1,
                "chunk_id": results["ids"][0][index],
                "distance": float(results["distances"][0][index]),
                "adjusted_distance": adjusted_distance,
                "source_title": metadata["source_title"],
                "source_type": metadata["source_type"],
                "url": metadata["url"],
                "block_index": metadata["block_index"],
                "character_count": metadata["character_count"],
                "text": text,
            }
        )
    matches.sort(key=lambda match: (match["adjusted_distance"], match["distance"]))
    trimmed = matches[:top_k]
    for index, match in enumerate(trimmed, start=1):
        match["rank"] = index
    return trimmed


def format_results(query: str, matches: list[dict[str, Any]]) -> str:
    lines = [f"Query: {query}", ""]
    for match in matches:
        lines.append(
            f"Rank {match['rank']} | distance={match['distance']:.4f} | "
            f"source={match['source_title']} | chunk={match['chunk_id']}"
        )
        lines.append(match["text"])
        lines.append("")
    lines.append("=" * 80)
    return "\n".join(lines)


def run_evaluation(model: SentenceTransformer, top_k: int, query_limit: int) -> list[dict[str, Any]]:
    selected_queries = EVALUATION_QUERIES[:query_limit]
    evaluation_rows: list[dict[str, Any]] = []
    rendered_sections: list[str] = []

    for query in selected_queries:
        matches = retrieve(query, model=model, top_k=top_k)
        evaluation_rows.append({"query": query, "results": matches})
        rendered_sections.append(format_results(query, matches))

    RETRIEVAL_EVAL_JSON.write_text(json.dumps(evaluation_rows, indent=2), encoding="utf-8")
    RETRIEVAL_EVAL_TXT.write_text("\n\n".join(rendered_sections).strip() + "\n", encoding="utf-8")

    return evaluation_rows


def command_index(_: argparse.Namespace) -> int:
    model = get_model()
    count = rebuild_collection(model=model)
    print(f"Indexed {count} chunks into {COLLECTION_NAME} using {MODEL_NAME}.")
    return 0


def command_query(args: argparse.Namespace) -> int:
    model = get_model()
    matches = retrieve(args.query, model=model, top_k=args.top_k)
    print(format_results(args.query, matches))
    return 0


def command_evaluate(args: argparse.Namespace) -> int:
    model = get_model()
    rows = run_evaluation(model=model, top_k=args.top_k, query_limit=args.query_limit)
    print(f"Saved retrieval evaluation to {RETRIEVAL_EVAL_TXT.relative_to(ROOT)}")
    print("")
    for row in rows:
        print(format_results(row["query"], row["results"]))
        print("")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and test the Chroma retrieval index.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="Embed chunks and rebuild the Chroma collection.")
    index_parser.set_defaults(func=command_index)

    query_parser = subparsers.add_parser("query", help="Run a single retrieval query.")
    query_parser.add_argument("query", help="Query text to send to the vector store.")
    query_parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help="Number of chunks to return.")
    query_parser.set_defaults(func=command_query)

    eval_parser = subparsers.add_parser("evaluate", help="Run retrieval on milestone evaluation questions.")
    eval_parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help="Number of chunks to return.")
    eval_parser.add_argument(
        "--query-limit",
        type=int,
        default=3,
        help="How many evaluation questions to run (starting from the top of the list).",
    )
    eval_parser.set_defaults(func=command_evaluate)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
