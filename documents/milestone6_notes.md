# Milestone 6 Notes

## Final Verification

Commands run for the final Milestone 6 pass:

- `./.venv/bin/python -m py_compile query.py app.py scripts/build_retrieval_index.py scripts/build_document_pipeline.py`
- `./.venv/bin/python scripts/build_retrieval_index.py evaluate --top-k 4 --query-limit 5`
- `./.venv/bin/python query.py "<question>"`
- `GRADIO_SERVER_PORT=8012 ./.venv/bin/python app.py`
- `curl -I --max-time 3 http://127.0.0.1:8012`

Interface check result:

- Gradio served locally at `http://127.0.0.1:8012`
- HTTP probe returned `200 OK`
- Uncovered-question check:
  - `What do students say about on-campus parking near the CS building?`
  - returned `I don't have enough information on that.`

## Final Evaluation Record

### 1. What background does CS 6515 expect before a student takes it?

- Expected answer:
  - Strong undergraduate algorithms background, including graph algorithms, dynamic programming, divide-and-conquer, discrete math, and asymptotic analysis.
- Actual response:
  - `CS 6515 expects students to have an undergraduate course on the design and analysis of algorithms, including familiarity with basic graph algorithms (DFS, BFS, Dijkstra's shortest path algorithm), dynamic programming, and divide and conquer algorithms. Students should also be comfortable with discrete mathematics and analyzing the asymptotic running time of algorithms [Source 1].`
- Source documents returned:
  - `CS 6515 Intro to Graduate Algorithms — https://omscs.gatech.edu/cs-6515-intro-graduate-algorithms`
- Retrieved chunk ids:
  - `03-cs-6515-intro-to-graduate-algorithms-chunk-006`
  - `03-cs-6515-intro-to-graduate-algorithms-chunk-002`
  - `03-cs-6515-intro-to-graduate-algorithms-chunk-001`
  - `03-cs-6515-intro-to-graduate-algorithms-chunk-004`
- Retrieval quality:
  - Relevant
- Response accuracy:
  - Accurate

### 2. What do students say makes CS 7641 Machine Learning difficult in practice?

- Expected answer:
  - Heavy workload, demanding reports/projects, deadline pressure, and the need to understand model behavior and experimentation rather than just coding.
- Actual response:
  - `According to the students, what makes CS 7641 Machine Learning difficult in practice includes the heavy workload with a strong focus on reports and frequent quizzes [Source 2], the need to manage time carefully to keep up with multiple deadlines [Source 2], and the excessive workload with multiple projects, quizzes, and exams [Source 4]. Additionally, students mention that the course requires a deep understanding of the material, going beyond implementation to thoughtful experimentation, interpretation, and well-structured reports [Source 3], and understanding why algorithms exist, when to use them, and how they behave in the wild [Source 1].`
- Source documents returned:
  - `Machine Learning reviews — https://www.omscentral.com/courses/machine-learning/reviews`
- Retrieved chunk ids:
  - `06-machine-learning-reviews-chunk-276`
  - `06-machine-learning-reviews-chunk-072`
  - `06-machine-learning-reviews-chunk-089`
  - `06-machine-learning-reviews-chunk-202`
- Retrieval quality:
  - Relevant
- Response accuracy:
  - Accurate

### 3. Is CS 6300 Software Development Process a good first OMSCS course?

- Expected answer:
  - Usually yes, especially for newer students, but experienced engineers may find it basic.
- Actual response:
  - `According to the provided context snippets, CS 6300 Software Development Process can be a good first OMSCS course. [Source 1] states that "it's a good class to take at the beginning of the OMSCS program," especially if you're not a seasoned engineer. [Source 2] also finds the course easy and useful, which could make it a suitable introduction to the program. However, [Source 3] mentions that they took it as their 2nd course, implying that it might not be the only option for a first course. Overall, the consensus leans towards it being a viable option for an early course in the OMSCS program [Source 1, Source 2].`
- Source documents returned:
  - `Software Development Process reviews — https://www.omscentral.com/courses/software-development-process/reviews`
- Retrieved chunk ids:
  - `08-software-development-process-reviews-chunk-051`
  - `08-software-development-process-reviews-chunk-088`
  - `08-software-development-process-reviews-chunk-197`
  - `08-software-development-process-reviews-chunk-052`
- Retrieval quality:
  - Relevant
- Response accuracy:
  - Accurate

### 4. What risk shows up repeatedly in student feedback for CS 6310 Software Architecture and Design?

- Expected answer:
  - Group-project problems plus concerns about grading, feedback, assignment clarity, and course value.
- Actual response:
  - `The risk that shows up repeatedly in student feedback for CS 6310 Software Architecture and Design is the risk of being assigned to a bad group, particularly with non-CS people, which can negatively impact the learning experience and grades [Source 1, Source 2]. Additionally, there is a risk of arbitrary and slow grading, with feedback being returned close to the due date of the next assignment, leaving little time to fix errors [Source 3, Source 4].`
- Source documents returned:
  - `Software Architecture and Design reviews — https://www.omscentral.com/courses/software-architecture-and-design/reviews`
- Retrieved chunk ids:
  - `10-software-architecture-and-design-reviews-chunk-018`
  - `10-software-architecture-and-design-reviews-chunk-163`
  - `10-software-architecture-and-design-reviews-chunk-117`
  - `10-software-architecture-and-design-reviews-chunk-125`
- Retrieval quality:
  - Relevant
- Response accuracy:
  - Accurate

### 5. How is CS 6603 AI, Ethics, and Society positioned compared with the other courses in this set?

- Expected answer:
  - Lighter-weight and less technical than classes like GA or ML, with more reading/discussion emphasis.
- Actual response:
  - `CS 6603 AI, Ethics, and Society is considered an easy course, but it didn't deliver as much value as hoped [Source 1]. Compared to other courses, it can be positioned as one of the easier ones, similar to Software Architecture and Design [Source 2] and Software Development Process [Source 4], which are also considered easy. However, it is much easier than Introduction to Graduate Algorithms [Source 3], which is considered very difficult.`
- Source documents returned:
  - `AI Ethics and Society reviews — https://www.omscentral.com/courses/ai-ethics-and-society/reviews`
  - `Software Architecture and Design reviews — https://www.omscentral.com/courses/software-architecture-and-design/reviews`
  - `Introduction to Graduate Algorithms reviews — https://www.omscentral.com/courses/introduction-to-graduate-algorithms/reviews`
  - `Software Development Process reviews — https://www.omscentral.com/courses/software-development-process/reviews`
- Retrieved chunk ids:
  - `12-ai-ethics-and-society-reviews-chunk-029`
  - `10-software-architecture-and-design-reviews-chunk-259`
  - `04-introduction-to-graduate-algorithms-reviews-chunk-320`
  - `08-software-development-process-reviews-chunk-088`
- Retrieval quality:
  - Partially relevant
- Response accuracy:
  - Partially accurate

## Final Failure Case

- Question:
  - `How is CS 6603 AI, Ethics, and Society positioned compared with the other courses in this set?`
- Why it failed:
  - Retrieval returned useful but indirect evidence about course difficulty, not direct side-by-side evidence about technical depth or reading/discussion emphasis.
  - Generation then turned those difficulty snippets into a shallow comparison, which is somewhat grounded but not as complete or precise as the expected answer.
- Pipeline stage:
  - Retrieval-to-generation handoff

## Demo Recording Script

Use the Gradio app and keep source citations visible.

Query order:

1. `What background does CS 6515 expect before a student takes it?`
2. `Is CS 6300 Software Development Process a good first OMSCS course?`
3. `What risk shows up repeatedly in student feedback for CS 6310 Software Architecture and Design?`
4. `How is CS 6603 AI, Ethics, and Society positioned compared with the other courses in this set?`

Talking points:

- Start on the home screen and point out `Answer`, `Retrieved from`, and `Retrieved snippets`
- Use `CS 6515` as the "works well" example because it maps directly to the official prerequisite chunk
- Show that the first three queries produce grounded answers with visible sources
- Use `CS 6603` as the honest failure case
- Explain that the system found some relevant evidence, but not enough direct comparison evidence, so the answer is only partially accurate
- End by opening `README.md` and scrolling through:
  - the evaluation table
  - the retrieved chunk list
  - the failure case explanation

Recording defaults:

- Use `GRADIO_SERVER_PORT=8012` if the default port range is busy
- Keep the demo to about 3 to 5 minutes
