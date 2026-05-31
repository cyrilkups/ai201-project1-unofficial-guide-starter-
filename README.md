# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

This project covers Georgia Tech OMSCS course-selection and workload advice, with a focus on the first-year questions students ask when deciding what to take and what to avoid pairing together. The official OMSCS site explains what each course is about, but it does not centralize the lived experience details students care about most: hidden workload, math intensity, project ambiguity, group-project risk, and whether a class feels like a good entry point for someone new to the program.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | OMSCS Machine Learning specialization page | Official page | https://omscs.gatech.edu/specialization-machine-learning |
| 2 | r/OMSCS Specializations and Courses Megathread | Reddit thread | https://www.reddit.com/r/OMSCS/comments/1pyef5z/course_specs_megathread_selection_choices/ |
| 3 | CS 6515: Intro to Graduate Algorithms | Official page | https://omscs.gatech.edu/cs-6515-intro-graduate-algorithms |
| 4 | Introduction to Graduate Algorithms reviews | Student review page | https://www.omscentral.com/courses/introduction-to-graduate-algorithms/reviews |
| 5 | CS 7641: Machine Learning | Official page | https://omscs.gatech.edu/cs-7641-machine-learning |
| 6 | Machine Learning reviews | Student review page | https://www.omscentral.com/courses/machine-learning/reviews |
| 7 | CS 6300: Software Development Process | Official page | https://omscs.gatech.edu/cs-6300-software-development-process |
| 8 | Software Development Process reviews | Student review page | https://www.omscentral.com/courses/software-development-process/reviews |
| 9 | CS 6310: Software Architecture and Design | Official page | https://omscs.gatech.edu/cs-6310-software-architecture-and-design |
| 10 | Software Architecture and Design reviews | Student review page | https://www.omscentral.com/courses/software-architecture-and-design/reviews |
| 11 | CS 6603: AI, Ethics, and Society | Official page | https://omscs.gatech.edu/cs-6603-ai-ethics-and-society |
| 12 | AI, Ethics, and Society reviews | Student review page | https://www.omscentral.com/courses/ai-ethics-and-society/reviews |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** 650 characters target per chunk

**Overlap:** 120 characters when a block has to be split

**Why these choices fit your documents:** My corpus mixes short official course pages with much longer student review pages, so I chunked by natural units first instead of splitting everything mechanically. Official OMSCS pages are cleaned into paragraph-sized sections, while OMSCentral pages are split into one review block at a time and then only split further if a single review runs long. I also capped OMSCentral ingestion at the 100 most recent reviews per course page so the corpus stays balanced and does not get overwhelmed by older repetitive reviews.

**Final chunk count:** 1,812 chunks across 11 loaded sources

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers`

**Production tradeoff reflection:** I used `all-MiniLM-L6-v2` because it is easy to run locally and was fast enough for a small corpus like this one. It did a good job on course-specific questions once I paired it with course-code-aware retrieval and a little query expansion for cases like prerequisites or “good first course” questions. If this were a real product, I would compare it against a stronger embedding model to see whether it handled opinion-heavy review text better, but I would still have to weigh that against speed, cost, and how much complexity I wanted in a student-facing tool.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

My generation step uses a strict system prompt in `query.py` with rules like: "Use only the provided context snippets," "Do not use outside knowledge, guesses, or generic advice," and "If the context is missing, weak, or does not directly answer the question, reply with exactly: `I don't have enough information on that.`" I also require inline source labels such as `[Source 1]` so the model has to tie each claim back to one of the retrieved snippets instead of answering from memory.

**How source attribution is surfaced in the response:**

Source attribution is enforced in two ways. First, the LLM sees each retrieved chunk wrapped in a labeled block like `[Source 1]`, plus the source title and URL. Second, after generation, the app programmatically returns a `Retrieved from` list built from the actual retrieved chunks, so the interface always shows which documents supported the answer even if the model's wording is short. I also filter out weak retrieval cases before generation: if the best chunks are low-signal or too distant, the system returns `I don't have enough information on that.` without asking the model to improvise.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What background does CS 6515 expect before a student takes it? | Strong undergraduate algorithms background, including graph algorithms, dynamic programming, divide-and-conquer, and discrete math. | The system answered with the official prerequisite list from the OMSCS page and cited the GA course page. | Relevant | Accurate |
| 2 | What do students say makes CS 7641 Machine Learning difficult in practice? | It is time-intensive, concept-heavy, and difficult because students have to understand and explain model behavior, not just code. | The system said students find ML hard because of the heavy workload and the need to understand why algorithms behave the way they do, not just write code. | Relevant | Accurate |
| 3 | Is CS 6300 Software Development Process a good first OMSCS course? | Usually yes for newer students, though experienced engineers may find it basic. | The system answered yes overall, while noting that experienced engineers may find it less valuable. | Relevant | Accurate |
| 4 | What risk shows up repeatedly in student feedback for CS 6310 Software Architecture and Design? | Group-project problems and mixed opinions about assignment clarity, grading, and course value. | The system identified bad group assignments, unclear project instructions, weak TA feedback, and slow or arbitrary grading as recurring risks. | Relevant | Accurate |
| 5 | How is CS 6603 AI, Ethics, and Society positioned compared with the other courses in this set? | It should come across as lighter-weight and less technical than classes like GA or ML, with more reading and discussion. | The system declined with `I don't have enough information on that.` instead of giving a comparison answer. | Partially relevant | Partially accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

How is CS 6603 AI, Ethics, and Society positioned compared with the other courses in this set?

**What the system returned:**

`I don't have enough information on that.`

**Root cause (tied to a specific pipeline stage):**

This failure came from the retrieval-plus-generation handoff, not from a broken API call. Retrieval did find some useful `CS 6603` review chunks and cross-course comparison chunks, but they were mostly short opinion snippets rather than explicit side-by-side comparisons. Because the generation prompt is intentionally strict, the model chose to decline instead of stitching together a comparison that was only indirectly supported.

**What you would change to fix it:**

I would improve the retrieval stage for comparison questions by adding course-level summary chunks or a small post-retrieval summarization step that groups evidence by course before sending it to the LLM. That would give the model clearer comparative context without relaxing the grounding rule.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*

**Instance 2**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*
