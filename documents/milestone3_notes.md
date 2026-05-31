# Milestone 3 Notes

## What I built

- `scripts/build_document_pipeline.py` reads `documents/source_manifest.csv`
- It fetches supported source pages, extracts text, cleans boilerplate, and writes local `.txt` files
- It saves chunked output to `artifacts/chunks.jsonl`
- It also writes `artifacts/chunk_summary.json` and `artifacts/chunk_samples.txt` for inspection

## What loaded successfully

- 11 sources loaded successfully
- 1 source was skipped: the Reddit megathread, because Reddit blocked requests from this environment

## Cleaning and chunking notes

- Official OMSCS pages were cleaned from their main content area and split into paragraph-style blocks
- OMSCentral pages were cleaned into one review block at a time
- To keep the corpus manageable, I limited OMSCentral pages to the 100 most recent reviews per course page
- Chunk size is 650 characters with 120 characters of overlap only when a single block is too long

## Output check

- Final chunk count: 1,812
- Raw extracted text files live in `documents/raw_text/`
- Cleaned text files live in `documents/cleaned/`
- Five readable sample chunks are saved in `artifacts/chunk_samples.txt`
