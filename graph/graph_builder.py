"""LangGraph StateGraph definition for the FotoOwl image-to-video pipeline."""
from __future__ import annotations

import logging
from pathlib import Path

from langgraph.graph import END, StateGraph

from graph.nodes import (
    compiler_fixer,
    image_analyser,
    intent_parser,
    renderer,
    script_generator,
    storyboard_writer,
    voice_generator,
)
from graph.state import PipelineState

logger = logging.getLogger(__name__)


def _route_after_compiler(state: PipelineState) -> str:
    """Conditional edge: decide where to go after compiler_fixer runs.

    • compile success              → renderer
    • compile failure + retries left → script_generator (with error context)
    • compile failure + no retries   → END (error_report already set)
    """
    compile_result = state.get("compile_result")
    if compile_result and compile_result.success:
        return "renderer"

    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)

    if retry_count < max_retries:
        logger.info(
            "graph: compilation failed, retrying script_generator (%d/%d)",
            retry_count,
            max_retries,
        )
        return "script_generator"

    logger.error("graph: max retries reached — terminating pipeline.")
    return END


def build_graph():
    """Construct and compile the FotoOwl LangGraph StateGraph.

    Returns a compiled graph ready for .invoke() calls.
    """
    graph = StateGraph(PipelineState)

    # ── Register nodes ────────────────────────────────────────────────────────
    graph.add_node("intent_parser", intent_parser)
    graph.add_node("image_analyser", image_analyser)
    graph.add_node("storyboard_writer", storyboard_writer)
    graph.add_node("voice_generator", voice_generator)
    graph.add_node("script_generator", script_generator)
    graph.add_node("compiler_fixer", compiler_fixer)
    graph.add_node("renderer", renderer)

    # ── Entry point ───────────────────────────────────────────────────────────
    graph.set_entry_point("intent_parser")

    # ── Static edges ──────────────────────────────────────────────────────────
    graph.add_edge("intent_parser", "image_analyser")
    graph.add_edge("image_analyser", "storyboard_writer")
    graph.add_edge("storyboard_writer", "voice_generator")
    graph.add_edge("voice_generator", "script_generator")
    graph.add_edge("script_generator", "compiler_fixer")

    # ── Conditional edge: compiler_fixer → renderer | script_generator | END ─
    graph.add_conditional_edges(
        "compiler_fixer",
        _route_after_compiler,
        {
            "renderer": "renderer",
            "script_generator": "script_generator",
            END: END,
        },
    )

    graph.add_edge("renderer", END)

    return graph.compile()


def get_graph_diagram() -> str:
    """Generate a Mermaid diagram of the pipeline and save it to README_graph.md.

    Returns the Mermaid source string.
    """
    compiled = build_graph()
    mermaid_source = compiled.get_graph().draw_mermaid()

    diagram_path = Path("README_graph.md")
    diagram_path.write_text(
        f"# FotoOwl Pipeline Graph\n\n```mermaid\n{mermaid_source}\n```\n",
        encoding="utf-8",
    )
    logger.info("Graph diagram saved to %s", diagram_path)
    return mermaid_source
