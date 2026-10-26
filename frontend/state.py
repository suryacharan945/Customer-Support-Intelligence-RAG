"""Streamlit Session State Management.

Centralizes session state initialization, chat turn records,
session identification, and feedback tracking.
"""

import uuid
import time
from typing import Dict, Any, List, Optional
import streamlit as st


def init_session_state() -> None:
    """Initialize all persistent session state variables if not already set."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "retrieval_mode" not in st.session_state:
        st.session_state.retrieval_mode = "multi_context"

    if "top_k" not in st.session_state:
        st.session_state.top_k = 5

    if "comparison_data" not in st.session_state:
        st.session_state.comparison_data = None

    if "feedback_submitted" not in st.session_state:
        st.session_state.feedback_submitted = {}

    if "last_error" not in st.session_state:
        st.session_state.last_error = None


def add_chat_turn(query: str, response: Dict[str, Any]) -> None:
    """
    Append a completed query and response turn to the conversation history.
    
    Args:
        query: User question string.
        response: Response dictionary from /api/v1/query.
    """
    turn_id = f"turn_{len(st.session_state.chat_history) + 1}_{uuid.uuid4().hex[:6]}"
    
    turn = {
        "turn_id": turn_id,
        "timestamp": time.strftime("%H:%M:%S"),
        "query": query,
        "answer": response.get("answer", ""),
        "retrieval_mode": response.get("retrieval_mode", "multi_context"),
        "selected_categories": response.get("selected_categories", []),
        "supporting_citations": response.get("supporting_citations", []),
        "candidate_citations": response.get("citations", []),
        "evidence_status": response.get("evidence_status", "SUFFICIENT"),
        "retrieval_latency_ms": response.get("retrieval_latency_ms", 0.0),
        "generation_latency_ms": response.get("generation_latency_ms"),
        "provider_status": response.get("provider_status", "UNKNOWN"),
        "contexts_used": response.get("contexts_used", 0),
        "is_mock": response.get("is_mock", False),
    }
    
    st.session_state.chat_history.append(turn)


def clear_chat_history() -> None:
    """Clear all chat turns and feedback records for the current session."""
    st.session_state.chat_history = []
    st.session_state.feedback_submitted = {}
    st.session_state.last_error = None


def mark_feedback_submitted(turn_id: str) -> None:
    """Record that feedback was successfully submitted for a given turn."""
    st.session_state.feedback_submitted[turn_id] = True


def is_feedback_submitted(turn_id: str) -> bool:
    """Check if feedback has already been submitted for a turn."""
    return st.session_state.feedback_submitted.get(turn_id, False)
