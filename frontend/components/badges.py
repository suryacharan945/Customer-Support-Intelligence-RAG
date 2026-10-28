"""Visual Badges and Status Indicators for Streamlit UI.

Provides standardized, accessible, and color-coded badge components.
"""

from typing import Optional


def get_lifecycle_badge_html(status: str, is_searchable: bool) -> str:
    """
    Generate HTML badge for document lifecycle status with explicit searchability warning.
    """
    status_lower = status.lower()
    
    if status_lower == "indexed" and is_searchable:
        return (
            '<span style="background-color:#dcfce7; color:#15803d; border:1px solid #86efac; '
            'padding:3px 10px; border-radius:12px; font-weight:600; font-size:12px;">'
            '✅ Indexed & Searchable</span>'
        )
    elif status_lower == "pending_index":
        return (
            '<span style="background-color:#fef9c3; color:#a16207; border:1px solid #fde047; '
            'padding:3px 10px; border-radius:12px; font-weight:600; font-size:12px;">'
            '⏳ Pending Indexing (Not Searchable)</span>'
        )
    elif status_lower == "processed":
        return (
            '<span style="background-color:#dbeafe; color:#1d4ed8; border:1px solid #93c5fd; '
            'padding:3px 10px; border-radius:12px; font-weight:600; font-size:12px;">'
            '⚙️ Processed (Not Searchable)</span>'
        )
    elif status_lower == "uploaded":
        return (
            '<span style="background-color:#f3f4f6; color:#4b5563; border:1px solid #d1d5db; '
            'padding:3px 10px; border-radius:12px; font-weight:600; font-size:12px;">'
            '📥 Uploaded (Not Searchable)</span>'
        )
    elif status_lower == "indexing_failed":
        return (
            '<span style="background-color:#fee2e2; color:#b91c1c; border:1px solid #fca5a5; '
            'padding:3px 10px; border-radius:12px; font-weight:600; font-size:12px;">'
            '❌ Indexing Failed</span>'
        )
    elif status_lower == "deleted":
        return (
            '<span style="background-color:#f3f4f6; color:#9ca3af; border:1px solid #e5e7eb; '
            'padding:3px 10px; border-radius:12px; font-weight:600; font-size:12px; text-decoration:line-through;">'
            '🗑️ Deleted</span>'
        )
    else:
        return (
            f'<span style="background-color:#f3f4f6; color:#4b5563; '
            f'padding:3px 10px; border-radius:12px; font-weight:600; font-size:12px;">'
            f'{status}</span>'
        )


def get_category_badge_html(category: str) -> str:
    """Generate HTML badge for document category."""
    cat_lower = category.lower()
    styles = {
        "troubleshooting": ("#fff7ed", "#c2410c", "#fed7aa", "🔧 Troubleshooting"),
        "warranty": ("#f0fdf4", "#15803d", "#bbf7d0", "🛡️ Warranty & SLA"),
        "product_manual": ("#eff6ff", "#1d4ed8", "#bfdbfe", "📖 Product Manual"),
        "faq": ("#faf5ff", "#7e22ce", "#e9d5ff", "❓ FAQ"),
    }
    bg, fg, border, label = styles.get(
        cat_lower, ("#f3f4f6", "#374151", "#e5e7eb", f"📁 {category.title()}")
    )
    return (
        f'<span style="background-color:{bg}; color:{fg}; border:1px solid {border}; '
        f'padding:2px 8px; border-radius:8px; font-weight:600; font-size:11px;">'
        f'{label}</span>'
    )


def get_provider_badge_html(status: str) -> str:
    """Generate HTML badge for LLM provider connectivity status."""
    st_upper = status.upper()
    if "LOCAL_GROUNDED_SYNTHESIS" in st_upper:
        return (
            '<span style="background-color:#f0fdf4; color:#15803d; border:1px solid #86efac; '
            'padding:3px 10px; border-radius:12px; font-weight:600; font-size:12px;">'
            '💻 Local Grounded Engine</span>'
        )
    elif "LOCAL_GROUNDED_FALLBACK" in st_upper:
        return (
            '<span style="background-color:#fffbeb; color:#b45309; border:1px solid #fcd34d; '
            'padding:3px 10px; border-radius:12px; font-weight:600; font-size:12px;">'
            '⚠️ Local Fallback (Colab Offline)</span>'
        )
    elif "READY_FOR_COLAB" in st_upper:
        return (
            '<span style="background-color:#eff6ff; color:#1d4ed8; border:1px solid #93c5fd; '
            'padding:3px 10px; border-radius:12px; font-weight:600; font-size:12px;">'
            '⚡ Colab GPU Standby</span>'
        )
    elif "MOCK" in st_upper:
        return (
            '<span style="background-color:#fffbeb; color:#b45309; border:1px solid #fcd34d; '
            'padding:3px 10px; border-radius:12px; font-weight:600; font-size:12px;">'
            '🧪 Test Mock Mode</span>'
        )
    elif "ONLINE" in st_upper:
        return (
            '<span style="background-color:#f0fdf4; color:#15803d; border:1px solid #86efac; '
            'padding:3px 10px; border-radius:12px; font-weight:600; font-size:12px;">'
            '🟢 Remote GPU Online</span>'
        )
    else:
        return (
            f'<span style="background-color:#f3f4f6; color:#4b5563; border:1px solid #d1d5db; '
            f'padding:3px 10px; border-radius:12px; font-weight:600; font-size:12px;">'
            f'⚪ {status}</span>'
        )


def get_evidence_badge_html(status: str) -> str:
    """Generate HTML badge for evidence groundedness status."""
    st_upper = status.upper()
    if st_upper == "SUFFICIENT":
        return (
            '<span style="background-color:#f0fdf4; color:#15803d; border:1px solid #86efac; '
            'padding:2px 8px; border-radius:10px; font-weight:600; font-size:11px;">'
            '🟢 Sufficient Grounding</span>'
        )
    elif st_upper == "PARTIAL":
        return (
            '<span style="background-color:#fffbeb; color:#b45309; border:1px solid #fcd34d; '
            'padding:2px 8px; border-radius:10px; font-weight:600; font-size:11px;">'
            '🟡 Partial Evidence</span>'
        )
    else:
        return (
            '<span style="background-color:#fef2f2; color:#b91c1c; border:1px solid #fca5a5; '
            'padding:2px 8px; border-radius:10px; font-weight:600; font-size:11px;">'
            '🔴 Insufficient Evidence</span>'
        )
