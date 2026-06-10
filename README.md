# The Unofficial Guide - Project 1

This project is a grounded question-answering system for Georgia Tech OMSCS course planning. It combines official OMSCS course pages with student review pages so the system can answer questions about prerequisites, workload, beginner-friendliness, and recurring course risks without relying on unsupported outside knowledge.

## Domain

The domain is Georgia Tech OMSCS course-selection and workload advice, especially the first-year questions students ask when deciding what to take and what to avoid pairing together. This knowledge is valuable because the official OMSCS pages explain what a course covers, but they do not centralize the lived-experience details students care about most: hidden workload, math intensity, project ambiguity, group-project risk, and whether a class feels like a good entry point for someone new to the program.

## Document Sources

I collected 12 sources for the corpus. The ingestion pipeline successfully loaded 11 of them. One Reddit thread remained in the manifest and planning spec, but it was skipped in this environment because Reddit blocked fetches from the project runtime.

| # | Source | Type | Focus | URL | Status |
|---|--------|------|-------|-----|--------|
| 1 | OMSCS Machine Learning specialization page | official page | specialization requirements and elective planning | https://omscs.gatech.edu/specialization-machine-learning | Loaded |
| 2 | r/OMSCS Specializations and Courses Megathread | reddit thread | student planning advice about course selection and sequencing | https://www.reddit.com/r/OMSCS/comments/1pyef5z/course_specs_megathread_selection_choices/ | Skipped: Reddit blocked this environment |
| 3 | CS 6515 Intro to Graduate Algorithms | official page | official expectations and background for GA | https://omscs.gatech.edu/cs-6515-intro-graduate-algorithms | Loaded |
| 4 | Introduction to Graduate Algorithms reviews | student review page | student difficulty and workload reports for GA | https://www.omscentral.com/courses/introduction-to-graduate-algorithms/reviews | Loaded |
| 5 | CS 7641 Machine Learning | official page | official overview and prerequisites for ML | https://omscs.gatech.edu/cs-7641-machine-learning | Loaded |
| 6 | Machine Learning reviews | student review page | student difficulty and workload reports for ML | https://www.omscentral.com/courses/machine-learning/reviews | Loaded |
| 7 | CS 6300 Software Development Process | official page | official overview for SDP | https://omscs.gatech.edu/cs-6300-software-development-process | Loaded |
| 8 | Software Development Process reviews | student review page | student comments on beginner friendliness and practical value | https://www.omscentral.com/courses/software-development-process/reviews | Loaded |
| 9 | CS 6310 Software Architecture and Design | official page | official overview for SAD | https://omscs.gatech.edu/cs-6310-software-architecture-and-design | Loaded |
| 10 | Software Architecture and Design reviews | student review page | student comments on group work and lecture quality | https://www.omscentral.com/courses/software-architecture-and-design/reviews | Loaded |
| 11 | CS 6603 AI Ethics and Society | official page | official overview for AI ethics course | https://omscs.gatech.edu/cs-6603-ai-ethics-and-society | Loaded |
| 12 | AI Ethics and Society reviews | student review page | student comments on workload and usefulness | https://www.omscentral.com/courses/ai-ethics-and-society/reviews | Loaded |

## Chunking Strategy

- Chunk size: 650 characters target per chunk
- Overlap: 120 characters, but only when a natural block had to be split
- Final chunk count: 1,812 chunks across 11 loaded sources

This chunk size fits the corpus because the documents are short official course pages plus much longer student review pages. A fixed mechanical split would have mixed unrelated review opinions together or broken small official paragraphs unnecessarily, so the pipeline chunks by natural units first. Official OMSCS pages are cleaned into paragraph-sized sections, while OMSCentral pages are split into one review block at a time and only split further if a single review runs long.

The 120-character overlap exists only for forced splits so important ideas do not get cut in half. That mattered most for longer review paragraphs where the key complaint and the workload or rating details sometimes appear at opposite ends of the same block.

Before chunking, `scripts/build_document_pipeline.py` fetches each source, strips navigation text and repeated boilerplate, removes leftover URLs and duplicate lines, and writes intermediate cleaned text to `documents/cleaned/`. I also capped OMSCentral ingestion at the 100 most recent reviews per course page so the corpus would stay balanced and not be dominated by one very large review page.

## Sample Chunks

These examples are copied from `artifacts/chunks.jsonl` and show the kinds of units the retriever actually indexes.

### Sample 1

- Source document: `CS 6515 Intro to Graduate Algorithms`
- Chunk id: `03-cs-6515-intro-to-graduate-algorithms-chunk-006`

```text
Students are expected to have an undergraduate course on the design and analysis of algorithms. In particular, they should be familiar with basic graph algorithms, including DFS, BFS, and Dijkstra's shortest path algorithm, and basic dynamic programming and divide and conquer algorithms (including solving recurrences). An undergraduate course in discrete mathematics is assumed, and students should be comfortable analyzing the asymptotic running time of algorithms.
```

### Sample 2

- Source document: `Machine Learning reviews`
- Chunk id: `06-machine-learning-reviews-chunk-276`

```text
Review 58
PLNqkSni4Yo64dBlTjLJ1g==May 1, 2025spring 2025
First things first: this is a graduate-level course in a CS program-so expect to engage your brain, not just your fingers. The goal isn't to write pristine code that passes every test case. Instead, you're encouraged to use all the libraries at your disposal to get things running quickly, so you can focus on the real challenge: understanding why algorithms exist, when to use them, and how they behave in the wild.
```

### Sample 3

- Source document: `Software Development Process reviews`
- Chunk id: `08-software-development-process-reviews-chunk-051`

```text
If you're a seasoned engineer, I wouldn't take this class unless it's part of your graduation requirements. Otherwise, it's a good class to take at the beginning of the OMSCS program.
Rating: 3 / 5Difficulty: 3 / 5Workload: 20 hours / week
```

### Sample 4

- Source document: `Software Architecture and Design reviews`
- Chunk id: `10-software-architecture-and-design-reviews-chunk-018`

```text
The project could be cool but the assignment has very unclear instructions and the feedback from the TAs is infrequent and unhelpful.
The class feels like it is just going through the motions of understanding software architecture but you don't actually learn much.
The class needs a reboot from a professor who cares about the course and the subject matter.
Rating: 2 / 5Difficulty: 2 / 5Workload: 15 hours / week
```

### Sample 5

- Source document: `CS 6603 AI Ethics and Society`
- Chunk id: `11-cs-6603-ai-ethics-and-society-chunk-008`

```text
In this class, you will be challenged to broaden your understanding of state-of-the-art AI/ML algorithms and solutions; considering the potential impacts they may have on society.
You will have ample opportunity to critically analyze various situations and viewpoints provided in papers, books, on the web, and from your own observations.
You will be able to practice your learned knowledge by writing coherent and well- structured critiques of situations and papers, leading and participating in class discussions, and designing your own algorithmic solutions.
```

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers`

I chose `all-MiniLM-L6-v2` because it runs locally, is fast enough for a small corpus, and works reasonably well for short course descriptions plus opinion-heavy review text. It was a good fit for Milestone 4 because it let me iterate on retrieval heuristics without waiting on an API or paying per embedding call.

For a production deployment, I would weigh several tradeoffs before changing models:

- Accuracy on review-style text: a stronger model might better connect phrases like "good first course," "manageable workload," and "easy A with useful projects."
- Latency and cost: API-hosted models may retrieve better, but they add ongoing latency, usage cost, and an external dependency.
- Local vs. hosted privacy: local embeddings keep the corpus and queries on the machine, while hosted embeddings trade privacy for convenience and potentially better quality.
- Context and multilingual coverage: if the corpus expanded beyond English course reviews or included longer documents, I would care more about multilingual performance and robustness on long, noisy inputs.

## Retrieval Test Results

The retriever uses `top_k = 4`, ChromaDB, and light query expansion in `scripts/build_retrieval_index.py`. Below are three representative retrieval tests from `artifacts/retrieval_eval.txt`.

### Query 1

**Query:** `What background does CS 6515 expect before a student takes it?`

| Rank | Chunk id | Source | Why it surfaced |
|---|---|---|---|
| 1 | `03-cs-6515-intro-to-graduate-algorithms-chunk-006` | CS 6515 Intro to Graduate Algorithms | Direct prerequisite chunk listing graph algorithms, dynamic programming, divide and conquer, discrete math, and asymptotic analysis |
| 2 | `03-cs-6515-intro-to-graduate-algorithms-chunk-002` | CS 6515 Intro to Graduate Algorithms | Course-level description of the algorithm families students will practice |
| 3 | `03-cs-6515-intro-to-graduate-algorithms-chunk-001` | CS 6515 Intro to Graduate Algorithms | Introductory course overview for algorithm design and analysis |
| 4 | `03-cs-6515-intro-to-graduate-algorithms-chunk-004` | CS 6515 Intro to Graduate Algorithms | Lower-signal official note about sample syllabi |

These results are relevant because the retriever stayed entirely within the official CS 6515 page and ranked the exact prerequisite chunk first. The first result alone directly answers the question, while ranks 2 and 3 add surrounding course context rather than pulling in unrelated review complaints.

### Query 2

**Query:** `What do students say makes CS 7641 Machine Learning difficult in practice?`

| Rank | Chunk id | Source | Why it surfaced |
|---|---|---|---|
| 1 | `06-machine-learning-reviews-chunk-276` | Machine Learning reviews | Explains that the real challenge is understanding algorithms, not just coding them |
| 2 | `06-machine-learning-reviews-chunk-072` | Machine Learning reviews | Describes heavy workload, report pressure, quizzes, and deadline stress |
| 3 | `06-machine-learning-reviews-chunk-089` | Machine Learning reviews | Highlights experimentation, interpretation, and report-writing demands |
| 4 | `06-machine-learning-reviews-chunk-202` | Machine Learning reviews | Adds evidence about project volume, quizzes, exams, and total workload |

These results are relevant because the retriever pulled four different review chunks that each cover a different part of "difficulty in practice": conceptual understanding, time pressure, experimentation/report writing, and raw workload. That spread is exactly what I wanted from a review-heavy corpus.

### Query 3

**Query:** `Is CS 6300 Software Development Process a good first OMSCS course?`

| Rank | Chunk id | Source | Why it surfaced |
|---|---|---|---|
| 1 | `08-software-development-process-reviews-chunk-051` | Software Development Process reviews | Explicitly says it is a good class to take at the beginning of OMSCS |
| 2 | `08-software-development-process-reviews-chunk-088` | Software Development Process reviews | Describes the course as easy but still useful |
| 3 | `08-software-development-process-reviews-chunk-197` | Software Development Process reviews | Perspective from a non-CS student who took it early in the program |
| 4 | `08-software-development-process-reviews-chunk-052` | Software Development Process reviews | Experienced-engineer perspective on what the course covers |

## Grounded Generation

Grounding is enforced by both prompt design and pipeline structure.

### System prompt

`query.py` uses this system prompt:

```text
You are answering questions about Georgia Tech OMSCS courses.

Rules:
1. Use only the provided context snippets.
2. Do not use outside knowledge, guesses, or generic advice.
3. If the context is missing, weak, or does not directly answer the question, reply with exactly:
I don't have enough information on that.
4. When you answer, cite the supporting source ids in square brackets, like [Source 1].
5. If the sources disagree, say that clearly and cite both sides.
6. Do not cite a source unless it directly supports the claim you just made.
```

### Pipeline structure

- Retrieval happens first through ChromaDB with `top_k = 4`.
- `select_context_matches()` filters out low-signal or weak matches before any LLM call.
- `format_context()` wraps each chunk in a labeled block such as `[Source 1]`, plus title, type, distance, URL, and excerpt.
- If no strong context remains after filtering, the system returns `I don't have enough information on that.` without asking the model to improvise.
- The Gradio app shows a programmatic `Retrieved from` list built from the actual retrieved chunks, so source attribution is not left to the model alone.

## Example Responses

These are example outputs from the end-to-end system, with source attribution visible in the answer text.

### Example 1

**Query:** `What background does CS 6515 expect before a student takes it?`

```text
CS 6515 expects students to have an undergraduate course on the design and analysis of algorithms, including familiarity with basic graph algorithms (DFS, BFS, Dijkstra's shortest path algorithm), dynamic programming, and divide and conquer algorithms. Students should also be comfortable with discrete mathematics and analyzing the asymptotic running time of algorithms [Source 1].
```

### Example 2

**Query:** `What do students say makes CS 7641 Machine Learning difficult in practice?`

```text
According to the students, what makes CS 7641 Machine Learning difficult in practice includes the heavy workload with a strong focus on reports and frequent quizzes [Source 2], the need to manage time carefully to keep up with multiple deadlines [Source 2], and the excessive workload with multiple projects, quizzes, and exams [Source 4]. Additionally, students mention that the course requires a deep understanding of the material, going beyond implementation to thoughtful experimentation, interpretation, and well-structured reports [Source 3], and understanding why algorithms exist, when to use them, and how they behave in the wild [Source 1].
```

### Example 3: Out-of-scope refusal

**Query:** `What do students say about on-campus parking near the CS building?`

```text
I don't have enough information on that.
```

## Query Interface

The main interface is the Gradio app in `app.py`.

### Input field

- `Your question`: a natural-language course-planning question such as `Is CS 6300 a good first OMSCS course?`

### Output fields

- `Answer`: the grounded response or the refusal response
- `Retrieved from`: a list of source titles and URLs used for the answer
- `Retrieved snippets`: the top retrieved chunk text, shown for debugging and transparency

There is also a CLI path through `query.py`, which prints the answer plus the final source list in the terminal.

### Sample interaction transcript

```text
Your question:
Is CS 6300 Software Development Process a good first OMSCS course?

Answer:
According to the provided context snippets, CS 6300 Software Development Process can be a good first OMSCS course. [Source 1] states that "it's a good class to take at the beginning of the OMSCS program," especially if you're not a seasoned engineer. [Source 2] also finds the course easy and useful, which could make it a suitable introduction to the program. However, [Source 3] mentions that they took it as their 2nd course, implying that it might not be the only option for a first course. Overall, the consensus leans towards it being a viable option for an early course in the OMSCS program [Source 1, Source 2].

Retrieved from:
- Software Development Process reviews - https://www.omscentral.com/courses/software-development-process/reviews

Retrieved snippets:
1. Software Development Process reviews | chunk=08-software-development-process-reviews-chunk-051
If you're a seasoned engineer, I wouldn't take this class unless it's part of your graduation requirements. Otherwise, it's a good class to take at the beginning of the OMSCS program.

2. Software Development Process reviews | chunk=08-software-development-process-reviews-chunk-088
However, personally, I think this course might be the easiest one in the OMSCS program for me. It feels like a second-semester freshman course that's been rebranded as a graduate course. I can't imagine any other course being easier than this. (Don't get me wrong, it's easy, but it's still useful.)
```

## Evaluation Report

These five evaluation questions come from `planning.md`.

| # | Question | Expected answer | System response | Retrieval quality | Accuracy judgment |
|---|----------|-----------------|-----------------|-------------------|-------------------|
| 1 | What background does CS 6515 expect before a student takes it? | Strong undergraduate algorithms background, including graph algorithms, dynamic programming, divide-and-conquer, discrete math, and asymptotic analysis. | `CS 6515 expects students to have an undergraduate course on the design and analysis of algorithms... Students should also be comfortable with discrete mathematics and analyzing the asymptotic running time of algorithms [Source 1].` | Relevant | Accurate |
| 2 | What do students say makes CS 7641 Machine Learning difficult in practice? | Heavy workload, demanding reports/projects, deadline pressure, and the need to understand model behavior and experimentation rather than just coding. | `According to the students, what makes CS 7641 Machine Learning difficult in practice includes the heavy workload with a strong focus on reports and frequent quizzes... and understanding why algorithms exist, when to use them, and how they behave in the wild [Source 1].` | Relevant | Accurate |
| 3 | Is CS 6300 Software Development Process a good first OMSCS course? | Usually yes, especially for newer students, though experienced engineers may find it basic. | `According to the provided context snippets, CS 6300 Software Development Process can be a good first OMSCS course... the consensus leans towards it being a viable option for an early course in the OMSCS program [Source 1, Source 2].` | Relevant | Accurate |
| 4 | What risk shows up repeatedly in student feedback for CS 6310 Software Architecture and Design? | Group-project problems plus concerns about grading, feedback, assignment clarity, and course value. | `The risk that shows up repeatedly... is the risk of being assigned to a bad group... Additionally, there is a risk of arbitrary and slow grading, with feedback being returned close to the due date of the next assignment [Source 3, Source 4].` | Relevant | Accurate |
| 5 | How is CS 6603 AI, Ethics, and Society positioned compared with the other courses in this set? | Lighter-weight and less technical than classes like GA or ML, with more reading/discussion emphasis. | `CS 6603 AI, Ethics, and Society is considered an easy course... it can be positioned as one of the easier ones... However, it is much easier than Introduction to Graduate Algorithms [Source 3].` | Partially relevant | Partially accurate |

Top retrieved chunk ids by question:

1. `03-cs-6515-intro-to-graduate-algorithms-chunk-006`, `03-cs-6515-intro-to-graduate-algorithms-chunk-002`, `03-cs-6515-intro-to-graduate-algorithms-chunk-001`, `03-cs-6515-intro-to-graduate-algorithms-chunk-004`
2. `06-machine-learning-reviews-chunk-276`, `06-machine-learning-reviews-chunk-072`, `06-machine-learning-reviews-chunk-089`, `06-machine-learning-reviews-chunk-202`
3. `08-software-development-process-reviews-chunk-051`, `08-software-development-process-reviews-chunk-088`, `08-software-development-process-reviews-chunk-197`, `08-software-development-process-reviews-chunk-052`
4. `10-software-architecture-and-design-reviews-chunk-018`, `10-software-architecture-and-design-reviews-chunk-163`, `10-software-architecture-and-design-reviews-chunk-117`, `10-software-architecture-and-design-reviews-chunk-125`
5. `12-ai-ethics-and-society-reviews-chunk-029`, `10-software-architecture-and-design-reviews-chunk-259`, `04-introduction-to-graduate-algorithms-reviews-chunk-320`, `08-software-development-process-reviews-chunk-088`

## Honest Failure Case

**Question:** `How is CS 6603 AI, Ethics, and Society positioned compared with the other courses in this set?`

**What the system returned:**

```text
CS 6603 AI, Ethics, and Society is considered an easy course, but it didn't deliver as much value as hoped [Source 1]. Compared to other courses, it can be positioned as one of the easier ones, similar to Software Architecture and Design [Source 2] and Software Development Process [Source 4], which are also considered easy. However, it is much easier than Introduction to Graduate Algorithms [Source 3].
```

**Why it happened:** This failure came from the retrieval-to-generation handoff. Retrieval found relevant chunks about `CS 6603` being easy and also found chunks from easier and harder comparison courses, but those chunks were indirect difficulty opinions rather than direct statements about technical depth or reading/discussion emphasis. The model then stitched those snippets into a shallow "easy versus hard" comparison, which stayed partially grounded but missed the richer comparison the question actually asked for.

**What I would change:** I would improve the retrieval stage for comparison questions by adding course-level summary chunks or a small post-retrieval summarization step that groups evidence by course before sending it to the LLM.

## Spec Reflection

### One way the spec helped

The spec helped most during retrieval and evaluation because it forced me to define concrete test questions before I built the final answer step. That made it much easier to tell whether a bad output came from weak retrieval, weak prompting, or simply a question my documents did not really cover.

### One way implementation diverged

The biggest practical divergence was the Gradio version. The milestone handout suggests `gradio>=6.9.0`, but this project environment is on Python 3.9 and Gradio 6 requires Python 3.10+, so I used `gradio==4.44.1` instead. I also ended up adding extra retrieval heuristics for comparison questions and low-signal official chunks because plain semantic search alone was not reliable enough on the review-heavy corpus.

## AI Usage

### Instance 1

**What I gave the AI:** I gave Codex the domain summary, the source manifest, and my chunking strategy from `planning.md`, including the 650-character target, 120-character overlap, and the fact that official pages and review pages should be chunked differently.

**What it produced:** It produced the ingestion and chunking pipeline in `scripts/build_document_pipeline.py`, plus cleaned-text outputs and chunk artifacts.

**What I changed or overrode:** I kept the natural-block-first approach, capped OMSCentral ingestion at the 100 most recent reviews per course, and treated the blocked Reddit source as a documented skip instead of pretending it had been loaded successfully.

### Instance 2

**What I gave the AI:** I gave Codex the retrieval approach, evaluation questions, and grounding requirement from `planning.md`, then asked it to wire retrieval, Groq generation, and a Gradio interface together.

**What it produced:** It produced the end-to-end query pipeline in `query.py`, the Gradio app in `app.py`, and the initial grounding prompt and source-attribution flow.

**What I changed or overrode:** I tightened the no-answer behavior so unsupported questions return `I don't have enough information on that.`, made the final source list programmatic instead of trusting the model alone, and pinned Gradio to a Python-3.9-compatible version after testing the environment.
