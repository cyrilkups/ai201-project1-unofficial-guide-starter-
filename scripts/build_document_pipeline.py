#!/usr/bin/env python3
"""Build the Milestone 3 document pipeline.

This script:
1. Reads the source manifest.
2. Fetches source pages when possible.
3. Extracts raw text and cleaned text.
4. Chunks documents using the planning.md strategy.
5. Saves chunk artifacts for later embedding/retrieval work.
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
import random
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "documents" / "source_manifest.csv"
RAW_HTML_DIR = ROOT / "artifacts" / "raw_html"
RAW_TEXT_DIR = ROOT / "documents" / "raw_text"
CLEANED_TEXT_DIR = ROOT / "documents" / "cleaned"
ARTIFACTS_DIR = ROOT / "artifacts"
CHUNKS_PATH = ARTIFACTS_DIR / "chunks.jsonl"
SUMMARY_PATH = ARTIFACTS_DIR / "chunk_summary.json"
SAMPLES_PATH = ARTIFACTS_DIR / "chunk_samples.txt"

CHUNK_SIZE = 650
CHUNK_OVERLAP = 120
RANDOM_SEED = 201
REQUEST_TIMEOUT = 30
MAX_OMSCENTRAL_REVIEWS = 100
USER_AGENT = (
    "Mozilla/5.0 (compatible; unofficial-guide-bot/1.0; "
    "+https://github.com/cyrilkups/ai201-project1-unofficial-guide-starter-)"
)


class SourceBlockedError(RuntimeError):
    """Raised when a source cannot be fetched cleanly."""


@dataclass
class SourceRecord:
    source_id: str
    title: str
    source_type: str
    focus: str
    url: str

    @property
    def slug(self) -> str:
        normalized_title = re.sub(r"[^a-z0-9]+", "-", self.title.lower()).strip("-")
        return f"{int(self.source_id):02d}-{normalized_title}"


class TextExtractor(HTMLParser):
    """Minimal HTML-to-text extractor with readable line breaks."""

    BLOCK_TAGS = {
        "article",
        "br",
        "dd",
        "div",
        "dt",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "li",
        "main",
        "ol",
        "p",
        "section",
        "table",
        "tr",
        "ul",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data)

    def get_text(self) -> str:
        return "".join(self.parts)


def ensure_dirs() -> None:
    for path in (RAW_HTML_DIR, RAW_TEXT_DIR, CLEANED_TEXT_DIR, ARTIFACTS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def read_manifest(path: Path) -> list[SourceRecord]:
    records: list[SourceRecord] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            records.append(
                SourceRecord(
                    source_id=row["id"].strip(),
                    title=row["title"].strip(),
                    source_type=row["type"].strip(),
                    focus=row["focus"].strip(),
                    url=row["url"].strip(),
                )
            )
    return records


def fetch_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if "reddit.com" in parsed.netloc:
        raise SourceBlockedError("Reddit blocks this environment; use a manual text export if needed.")

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    context = ssl._create_unverified_context()

    try:
        with urllib.request.urlopen(request, context=context, timeout=REQUEST_TIMEOUT) as response:
            body = response.read()
    except urllib.error.HTTPError as exc:
        raise SourceBlockedError(f"HTTP {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise SourceBlockedError(f"Fetch failed for {url}: {exc.reason}") from exc

    return body.decode("utf-8", errors="ignore")


def save_text(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def html_to_text(fragment: str) -> str:
    parser = TextExtractor()
    parser.feed(fragment)
    parser.close()
    text = parser.get_text()
    text = html.unescape(text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_main_fragment(html_text: str, start_pattern: str, end_pattern: str) -> str:
    start_match = re.search(start_pattern, html_text, flags=re.IGNORECASE)
    if not start_match:
        return html_text

    start = start_match.start()
    end_match = re.search(end_pattern, html_text[start:], flags=re.IGNORECASE)
    if not end_match:
        return html_text[start:]

    end = start + end_match.start()
    return html_text[start:end]


def split_paragraphs(text: str) -> list[str]:
    blocks: list[str] = []
    for piece in re.split(r"\n{2,}", text):
        normalized = clean_block(piece)
        if normalized:
            blocks.append(normalized)
    return blocks


def clean_block(text: str) -> str:
    text = html.unescape(text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n\s+", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip(" -\n")

    lines = []
    seen: set[str] = set()
    skip_phrases = {
        "open main menu",
        "skip to main navigation",
        "skip to main content",
        "something missing or incorrect?",
        "tell us more.",
        "gt login",
        "home",
        "reviews",
        "add review",
        "file a ticket",
        "you've been blocked by network security.",
    }

    for raw_line in text.splitlines():
        line = raw_line.strip()
        normalized = re.sub(r"\s+", " ", line).strip()
        if not normalized:
            continue
        lower = normalized.lower()
        if lower in skip_phrases:
            continue
        if lower.startswith("http://") or lower.startswith("https://"):
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        lines.append(normalized)

    cleaned = "\n".join(lines).strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    if len(cleaned) < 40:
        return ""
    return cleaned


def extract_omscs_blocks(source: SourceRecord, html_text: str) -> tuple[list[str], list[str]]:
    main_fragment = extract_main_fragment(html_text, r'<div role="main"', r"<footer|id=\"gt-footer\"")
    raw_text = html_to_text(main_fragment)
    raw_blocks = split_paragraphs(raw_text)

    cleaned_blocks: list[str] = []
    for block in raw_blocks:
        if "GT LOGIN" in block:
            continue
        cleaned = clean_block(block)
        if cleaned:
            cleaned_blocks.append(cleaned)

    return raw_blocks, cleaned_blocks


def extract_omscentral_blocks(source: SourceRecord, html_text: str) -> tuple[list[str], list[str]]:
    main_fragment = extract_main_fragment(html_text, r"<main\b", r"</main>")
    if "blocked by network security" in main_fragment.lower():
        raise SourceBlockedError("OMSCentral returned a blocked page.")

    raw_blocks: list[str] = []

    title_match = re.search(r"<h3[^>]*>(.*?)</h3>", main_fragment, flags=re.IGNORECASE | re.DOTALL)
    title = html_to_text(title_match.group(1)) if title_match else source.title

    facts_match = re.search(r"<dl[^>]*>(.*?)</dl>", main_fragment, flags=re.IGNORECASE | re.DOTALL)
    if facts_match:
        facts_text = html_to_text(facts_match.group(0))
        facts_block = clean_block(f"{title}\n{facts_text}")
        if facts_block:
            raw_blocks.append(facts_block)

    articles = re.findall(r"<article\b.*?</article>", main_fragment, flags=re.IGNORECASE | re.DOTALL)
    selected_articles = articles[:MAX_OMSCENTRAL_REVIEWS]
    for article_index, article_html in enumerate(selected_articles, start=1):
        article_text = html_to_text(article_html)
        article_text = clean_block(article_text)
        if not article_text:
            continue
        raw_blocks.append(f"Review {article_index}\n{article_text}")

    cleaned_blocks = [clean_block(block) for block in raw_blocks]
    cleaned_blocks = [block for block in cleaned_blocks if block]
    return raw_blocks, cleaned_blocks


def extract_source_blocks(source: SourceRecord, html_text: str) -> tuple[list[str], list[str]]:
    hostname = urllib.parse.urlparse(source.url).netloc.lower()
    if "omscentral.com" in hostname:
        return extract_omscentral_blocks(source, html_text)
    if "omscs.gatech.edu" in hostname:
        return extract_omscs_blocks(source, html_text)
    raise SourceBlockedError(f"No extractor implemented for {hostname}")


def choose_split_point(text: str, max_len: int) -> int:
    preferred_breaks = ["\n\n", "\n", ". ", "? ", "! ", "; ", ": ", ", ", " "]
    floor = int(max_len * 0.55)
    candidate = text[:max_len]

    for marker in preferred_breaks:
        position = candidate.rfind(marker)
        if position >= floor:
            return position + len(marker)

    fallback = candidate.rfind(" ")
    if fallback > 0:
        return fallback + 1
    return max_len


def split_line_into_units(line: str, max_len: int) -> list[str]:
    if len(line) <= max_len:
        return [line]

    sentences = re.split(r"(?<=[.!?])\s+", line)
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
    if len(sentences) > 1:
        return sentences

    pieces: list[str] = []
    start = 0
    while start < len(line):
        remaining = len(line) - start
        if remaining <= max_len:
            pieces.append(line[start:].strip())
            break
        window = line[start : start + max_len]
        split_at = choose_split_point(window, max_len)
        end = start + split_at
        pieces.append(line[start:end].strip())
        start = end
    return [piece for piece in pieces if piece]


def block_units(text: str, max_len: int) -> list[str]:
    units: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        units.extend(split_line_into_units(line, max_len))
    return units


def split_long_block(text: str, max_len: int, overlap: int) -> list[str]:
    if len(text) <= max_len:
        return [text]

    units = block_units(text, max_len)
    chunks: list[str] = []
    current_units: list[str] = []
    current_length = 0

    for unit in units:
        separator_length = 1 if current_units else 0
        projected = current_length + separator_length + len(unit)
        if projected <= max_len:
            current_units.append(unit)
            current_length = projected
            continue

        if current_units:
            chunks.append("\n".join(current_units).strip())
            overlap_units: list[str] = []
            overlap_length = 0
            for previous_unit in reversed(current_units):
                needed = len(previous_unit) + (1 if overlap_units else 0)
                if overlap_length + needed > overlap:
                    break
                overlap_units.insert(0, previous_unit)
                overlap_length += needed
            current_units = overlap_units.copy()
            current_length = len("\n".join(current_units)) if current_units else 0

        if current_units:
            separator_length = 1
            projected = current_length + separator_length + len(unit)
            if projected <= max_len:
                current_units.append(unit)
                current_length = projected
                continue

        current_units = [unit]
        current_length = len(unit)

    if current_units:
        chunks.append("\n".join(current_units).strip())

    return [chunk for chunk in chunks if chunk]


def chunk_blocks(source: SourceRecord, cleaned_blocks: list[str]) -> list[dict[str, object]]:
    chunks: list[dict[str, object]] = []
    chunk_counter = 1

    for block_index, block in enumerate(cleaned_blocks, start=1):
        for piece in split_long_block(block, CHUNK_SIZE, CHUNK_OVERLAP):
            chunk_hash = hashlib.md5(piece.encode("utf-8")).hexdigest()[:10]
            chunks.append(
                {
                    "chunk_id": f"{source.slug}-chunk-{chunk_counter:03d}",
                    "source_id": source.source_id,
                    "source_slug": source.slug,
                    "source_title": source.title,
                    "source_type": source.source_type,
                    "focus": source.focus,
                    "url": source.url,
                    "block_index": block_index,
                    "character_count": len(piece),
                    "text_hash": chunk_hash,
                    "text": piece,
                }
            )
            chunk_counter += 1

    return chunks


def write_jsonl(path: Path, rows: Iterable[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def write_chunk_samples(chunks: list[dict[str, object]]) -> None:
    random.seed(RANDOM_SEED)
    def looks_representative(chunk_text: str) -> bool:
        stripped = chunk_text.strip()
        banned_phrases = (
            "Academic Honor Code",
            "All Georgia Tech students are expected",
            "Course Content",
        )
        if len(stripped) < 120:
            return False
        if stripped[0].islower():
            return False
        if stripped.endswith(":"):
            return False
        if any(phrase in stripped for phrase in banned_phrases):
            return False
        return stripped.endswith((".", "!", "?", "week"))

    candidates = [chunk for chunk in chunks if looks_representative(str(chunk["text"]))]
    population = candidates if len(candidates) >= 5 else chunks
    sample_count = min(5, len(population))
    sample_chunks = random.sample(population, sample_count)

    lines: list[str] = []
    for index, chunk in enumerate(sample_chunks, start=1):
        lines.append(f"Sample {index}")
        lines.append(f"Chunk ID: {chunk['chunk_id']}")
        lines.append(f"Source: {chunk['source_title']}")
        lines.append(f"Characters: {chunk['character_count']}")
        lines.append(chunk["text"])
        lines.append("")
        lines.append("-" * 80)
        lines.append("")

    save_text(SAMPLES_PATH, "\n".join(lines).strip())


def build_pipeline() -> int:
    ensure_dirs()
    sources = read_manifest(MANIFEST_PATH)

    all_chunks: list[dict[str, object]] = []
    loaded_sources: list[str] = []
    skipped_sources: list[dict[str, str]] = []

    for source in sources:
        print(f"Processing {source.source_id}: {source.title}")
        try:
            html_text = fetch_url(source.url)
            save_text(RAW_HTML_DIR / f"{source.slug}.html", html_text)
            raw_blocks, cleaned_blocks = extract_source_blocks(source, html_text)
        except SourceBlockedError as exc:
            print(f"  Skipped: {exc}")
            skipped_sources.append(
                {
                    "source_id": source.source_id,
                    "title": source.title,
                    "url": source.url,
                    "reason": str(exc),
                }
            )
            continue

        raw_text = "\n\n".join(raw_blocks)
        cleaned_text = "\n\n".join(cleaned_blocks)
        save_text(RAW_TEXT_DIR / f"{source.slug}.txt", raw_text)
        save_text(CLEANED_TEXT_DIR / f"{source.slug}.txt", cleaned_text)

        chunks = chunk_blocks(source, cleaned_blocks)
        print(f"  Raw blocks: {len(raw_blocks)} | Cleaned blocks: {len(cleaned_blocks)} | Chunks: {len(chunks)}")
        all_chunks.extend(chunks)
        loaded_sources.append(source.title)

    write_jsonl(CHUNKS_PATH, all_chunks)
    write_chunk_samples(all_chunks)

    summary = {
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "max_omscentral_reviews_per_page": MAX_OMSCENTRAL_REVIEWS,
        "loaded_source_count": len(loaded_sources),
        "skipped_source_count": len(skipped_sources),
        "total_chunk_count": len(all_chunks),
        "loaded_sources": loaded_sources,
        "skipped_sources": skipped_sources,
        "random_seed": RANDOM_SEED,
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("")
    print(f"Loaded sources: {len(loaded_sources)}")
    print(f"Skipped sources: {len(skipped_sources)}")
    print(f"Total chunks: {len(all_chunks)}")
    print(f"Chunk samples written to: {SAMPLES_PATH.relative_to(ROOT)}")

    if all_chunks:
        print("")
        print("Five sample chunks:")
        print(SAMPLES_PATH.read_text(encoding="utf-8"))

    if len(all_chunks) < 50:
        print("Warning: fewer than 50 chunks were produced. Check whether chunks are too large.")
    if len(all_chunks) > 2000:
        print("Warning: more than 2,000 chunks were produced. Check whether chunks are too small.")

    return 0


if __name__ == "__main__":
    sys.exit(build_pipeline())
