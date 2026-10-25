"""Prompt engineering templates for Multi-Context Prompting (MCP) and RAG synthesis."""

class PromptTemplates:
    """Standardized prompt templates for customer support reasoning."""

    SYSTEM_PROMPT = """You are an advanced enterprise AI customer support engineer.
Your task is to answer user inquiries accurately and concisely based strictly on the provided multi-source documentation.

Guiding Principles:
1. Multi-Context Reasoning: Synthesize facts across product manuals, troubleshooting guides, FAQs, and warranty policies.
2. Factuality & Trust: Never invent steps or speculate. If the context does not contain the answer, state clearly that information is unavailable and offer to escalate.
3. Citations: Reference the exact document source for every actionable instruction.
4. Structure: Provide clear step-by-step guidance.
"""

    QUERY_EXPANSION_PROMPT = """Analyze the customer support query below. Produce an expanded search query that includes relevant technical synonyms, components, and potential fault categories.

Original Query: {query}
Expanded Query:"""

    MCP_SYNTHESIS_TEMPLATE = """Context Sections (Assembled via Multi-Context Prompting):
{mcp_context}

Customer Inquiry:
{user_query}

Response Format:
- Direct Answer / Remediation Steps
- Relevant Source Citations
- Confidence Assessment (High, Medium, Low)
"""
