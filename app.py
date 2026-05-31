#!/usr/bin/env python3
"""Gradio interface for the OMSCS unofficial guide."""

from __future__ import annotations

import os

import gradio as gr

from query import ask


def handle_query(question: str):
    result = ask(question)
    sources = "\n".join(f"- {source}" for source in result["sources"]) or "No sources returned."
    debug = result["retrieval_debug"] or "No retrieval context available."
    return result["answer"], sources, debug


with gr.Blocks(title="OMSCS Unofficial Guide") as demo:
    gr.Markdown(
        """
        # OMSCS Unofficial Guide
        Ask course-planning questions grounded in the local Georgia Tech OMSCS corpus.
        The answer box is grounded by retrieved documents, and the source box shows which pages were used.
        """
    )
    question = gr.Textbox(
        label="Your question",
        placeholder="Example: Is CS 6300 a good first OMSCS course?",
        lines=2,
    )
    ask_button = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=5)
    debug = gr.Textbox(label="Retrieved snippets", lines=14)

    ask_button.click(handle_query, inputs=question, outputs=[answer, sources, debug])
    question.submit(handle_query, inputs=question, outputs=[answer, sources, debug])

    gr.Examples(
        examples=[
            "What background does CS 6515 expect before a student takes it?",
            "Is CS 6300 Software Development Process a good first OMSCS course?",
            "What risk shows up repeatedly in student feedback for CS 6310 Software Architecture and Design?",
            "What do students say about on-campus parking near the CS building?",
        ],
        inputs=question,
    )


if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=int(os.getenv("GRADIO_SERVER_PORT", "7860")),
    )
