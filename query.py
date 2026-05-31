#!/usr/bin/env python3
"""Run grounded OMSCS course-planning queries end to end."""

from __future__ import annotations

import argparse
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from scripts.build_retrieval_index import DEFAULT_TOP_K, get_model, retrieve


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

GENERATION_MODEL = "llama-3.3-70b-versatile"
NO_ANSWER_TEXT = "I don't have enough information on that."
MAX_CONTEXT_MATCHES = 4
MAX_CONTEXT_CHARACTERS = 3_800

SYSTEM_PROMPT = """You are answering questions about Georgia Tech OMSCS courses.

Rules:
1. Use only the provided context snippets.
2. Do not use outside knowledge, guesses, or generic advice.
3. If the context is missing, weak, or does not directly answer the question, reply with exactly:
I don't have enough information on that.
4. When you answer, cite the supporting source ids in square brackets, like [Source 1].
5. If the sources disagree, say that clearly and cite both sides.
6. Do not cite a source unless it directly supports the claim you just made.
"""


@lru_cache(maxsize=1)
def get_embedding_model():
    return get_model()


@lru_cache(maxsize=1)
def get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to .env before running generation.")
    return Groq(api_key=api_key)


def select_context_matches(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    strong_matches = [
        match for match in matches if not match.get("low_signal", False) and match["distance"] <= 0.5
    ]
    if strong_matches:
        return strong_matches[:MAX_CONTEXT_MATCHES]

    if matches and matches[0]["distance"] <= 0.45:
        return [match for match in matches[:MAX_CONTEXT_MATCHES] if not match.get("low_signal", False)]

    return []


def format_context(matches: list[dict[str, Any]]) -> str:
    sections: list[str] = []
    running_chars = 0

    for index, match in enumerate(matches, start=1):
        section = "\n".join(
            [
                f"[Source {index}]",
                f"Title: {match['source_title']}",
                f"Type: {match['source_type']}",
                f"Distance: {match['distance']:.4f}",
                f"URL: {match['url']}",
                "Excerpt:",
                match["text"],
            ]
        )
        if sections and running_chars + len(section) > MAX_CONTEXT_CHARACTERS:
            break
        sections.append(section)
        running_chars += len(section)

    return "\n\n".join(sections)


def format_source_list(matches: list[dict[str, Any]]) -> list[str]:
    seen: set[tuple[str, str]] = set()
    sources: list[str] = []
    for match in matches:
        key = (match["source_title"], match["url"])
        if key in seen:
            continue
        seen.add(key)
        sources.append(f"{match['source_title']} — {match['url']}")
    return sources


def build_user_prompt(question: str, context: str) -> str:
    return "\n\n".join(
        [
            f"Question: {question}",
            "Context snippets:",
            context,
            "Answer using only the context above.",
        ]
    )


def generate_answer(question: str, matches: list[dict[str, Any]]) -> str:
    context = format_context(matches)
    if not context:
        return NO_ANSWER_TEXT

    response = get_groq_client().chat.completions.create(
        model=GENERATION_MODEL,
        temperature=0.1,
        max_tokens=450,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(question, context)},
        ],
    )
    answer = (response.choices[0].message.content or "").strip()
    if not answer:
        return NO_ANSWER_TEXT
    return answer


def retrieval_debug_text(matches: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for match in matches:
        lines.append(
            f"{match['rank']}. {match['source_title']} | distance={match['distance']:.4f} | chunk={match['chunk_id']}"
        )
        lines.append(match["text"])
        lines.append("")
    return "\n".join(lines).strip()


def ask(question: str, top_k: int = DEFAULT_TOP_K) -> dict[str, Any]:
    cleaned_question = question.strip()
    if not cleaned_question:
        return {
            "question": question,
            "answer": "Ask a question about OMSCS courses or course planning.",
            "sources": [],
            "retrieved_chunks": [],
            "retrieval_debug": "",
            "grounded": False,
        }

    matches = retrieve(cleaned_question, model=get_embedding_model(), top_k=top_k)
    context_matches = select_context_matches(matches)

    if not context_matches:
        return {
            "question": cleaned_question,
            "answer": NO_ANSWER_TEXT,
            "sources": [],
            "retrieved_chunks": matches,
            "retrieval_debug": retrieval_debug_text(matches),
            "grounded": False,
        }

    answer = generate_answer(cleaned_question, context_matches)
    grounded = answer != NO_ANSWER_TEXT
    return {
        "question": cleaned_question,
        "answer": answer,
        "sources": format_source_list(context_matches) if grounded else [],
        "retrieved_chunks": context_matches,
        "retrieval_debug": retrieval_debug_text(context_matches),
        "grounded": grounded,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Ask the OMSCS unofficial guide a grounded question.")
    parser.add_argument("question", help="Question to answer from the retrieved corpus.")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help="How many chunks to retrieve.")
    args = parser.parse_args()

    result = ask(args.question, top_k=args.top_k)
    print(result["answer"])
    print("")
    print("Sources:")
    if result["sources"]:
        for source in result["sources"]:
            print(f"- {source}")
    else:
        print("- None")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
