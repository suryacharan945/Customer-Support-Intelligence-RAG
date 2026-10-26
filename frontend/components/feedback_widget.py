"""User Feedback and Active Learning Loop Widget.

Enables customer support agents or evaluators to rate responses,
submit corrections, and flag hallucinations.
"""

from typing import Optional, Dict, Any
import streamlit as st
from frontend.api_client import APIClient, APIClientError
from frontend.state import is_feedback_submitted, mark_feedback_submitted


def render_feedback_widget(
    api_client: APIClient,
    turn_id: str,
    query: str,
) -> None:
    """
    Render feedback submission form for a specific chat turn.
    
    Args:
        api_client: Instantiated API client.
        turn_id: Identifier for this chat response turn.
        query: User query string.
    """
    if is_feedback_submitted(turn_id):
        st.success("✨ Feedback recorded! Thank you for helping improve response accuracy.")
        return

    with st.expander("⭐ Rate & Provide Feedback on this Response", expanded=False):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            rating = st.select_slider(
                "Response Quality (1=Poor, 5=Excellent)",
                options=[1, 2, 3, 4, 5],
                value=5,
                key=f"rating_{turn_id}",
            )
            flagged = st.checkbox(
                "🚩 Flag as factually incorrect or unsupported",
                key=f"flag_{turn_id}",
            )

        with col2:
            comment = st.text_input(
                "Optional Comments / Notes",
                placeholder="e.g. Grounded citations, accurate troubleshooting steps",
                key=f"comment_{turn_id}",
            )
            correction = st.text_input(
                "Suggested Answer Correction (if incorrect)",
                placeholder="e.g. For error E-101, also check sensor lever alignment",
                key=f"corr_{turn_id}",
            )

        submit_btn = st.button("Submit Feedback", key=f"btn_fb_{turn_id}")

        if submit_btn:
            try:
                res = api_client.submit_feedback(
                    query_id=turn_id,
                    rating=rating,
                    comment=comment.strip() if comment else None,
                    flagged_incorrect=flagged,
                    correction=correction.strip() if correction else None,
                )
                mark_feedback_submitted(turn_id)
                st.success("✅ Feedback successfully logged to active learning queue!")
                st.rerun()
            except APIClientError as e:
                st.error(f"Failed to submit feedback: {str(e)}")
