# Milestone 4 Notes

## What I built

- `scripts/build_retrieval_index.py` builds a ChromaDB collection from `artifacts/chunks.jsonl`
- It uses `all-MiniLM-L6-v2` from `sentence-transformers`
- It stores each chunk with source metadata, including source title, source type, URL, block index, and course code

## Retrieval setup

- Vector store: local `chroma_db/`
- Default retrieval depth: top 4 chunks
- Query behavior:
  - If a query names a course code like `CS 6515`, retrieval filters to that course
  - Background/prerequisite questions prefer the official course page
  - “What do students say...” style questions prefer review pages
  - I also added small query expansion for a few common question types so the model matches the right chunks more reliably

## Retrieval check

I tested retrieval with 3 evaluation questions and saved the results in:

- `artifacts/retrieval_eval.txt`
- `artifacts/retrieval_eval.json`

Summary of the 3 checks:

1. **CS 6515 background question**
   - Top chunk came from the official course page
   - Top distance: `0.2778`
   - The returned chunk explicitly described the undergraduate algorithms and discrete math background students are expected to have

2. **CS 7641 difficulty question**
   - Top chunks came from Machine Learning review pages
   - Top distance: `0.2686`
   - The results focused on why students find the course hard in practice, especially the conceptual workload and the way the course is structured

3. **CS 6300 first-course question**
   - Top chunks came from Software Development Process review pages
   - Top distance: `0.2664`
   - The results clearly supported the idea that many students see it as an approachable early OMSCS course

## What I learned

- Pure semantic search was not enough by itself for every question
- Course-code-aware filtering helped a lot
- Official-page filtering worked better for prerequisite/background questions
- Review-page filtering worked better for “student opinion” questions
