"""
Reusable UI helper components for LeaseGuard AI.

Centralizes component rendering across all pages to ensure design consistency,
proper hierarchy, and crisp financial formatting.
"""

from typing import Any, Dict, List, Optional
import streamlit as st


# ---------------------------------------------------------------------------
# Formatting Helpers
# ---------------------------------------------------------------------------

def format_currency(amount: Any) -> str:
    """Format any numeric value cleanly as currency ($X,XXX.XX or $0.00)."""
    try:
        val = float(amount or 0.0)
        return f"${val:,.2f}"
    except (ValueError, TypeError):
        return "$0.00"


def format_currency_compact(amount: Any) -> str:
    """Format large numbers with compact suffix if >= 10,000."""
    try:
        val = float(amount or 0.0)
        if abs(val) >= 1_000_000:
            return f"${val / 1_000_000:.2f}M"
        elif abs(val) >= 10_000:
            return f"${val / 1_000:.1f}k"
        else:
            return f"${val:,.0f}"
    except (ValueError, TypeError):
        return "$0"


# ---------------------------------------------------------------------------
# Page & Section Headers
# ---------------------------------------------------------------------------

def render_page_header(title: str, subtitle: str = "", icon: str = "") -> None:
    """
    Render a standard enterprise page header with icon badge and subtitle.

    Args:
        title: Main page title (e.g., 'Dashboard')
        subtitle: Explanatory subtitle for the page
        icon: Single character or emoji representing the section
    """
    icon_badge_html = f'<div class="page-header-icon-badge">{icon}</div>' if icon else ""
    subtitle_html = f'<p class="page-header-subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div class="page-header">
            <div class="page-header-content">
                {icon_badge_html}
                <div>
                    <h1 class="page-header-title">{title}</h1>
                    {subtitle_html}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, description: str = "") -> None:
    """
    Render a clean section sub-heading within a page.

    Args:
        title: Section title
        description: Optional explanatory context
    """
    desc_html = f'<p class="section-desc">{description}</p>' if description else ""
    st.markdown(
        f"""
        <div class="section-header-block">
            <h3 class="section-header-title">{title}</h3>
            {desc_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# KPI & Metric Cards
# ---------------------------------------------------------------------------

def render_kpi_card(
    label: str,
    value: str,
    context: str = "",
    icon: str = "",
    accent_color: str = "",
) -> None:
    """
    Render a professional KPI card with border accent and micro-hover effect.

    Args:
        label: Metric label (e.g. 'Potential Recovery')
        value: Primary number/value to display
        context: Context line (e.g. '12 flagged findings')
        icon: Optional small icon / symbol
        accent_color: Optional CSS color for the left accent stripe
    """
    accent_style = f"border-left-color: {accent_color};" if accent_color else ""
    icon_html = f'<div class="kpi-icon">{icon}</div>' if icon else ""
    context_html = f'<div class="kpi-context">{context}</div>' if context else ""
    st.markdown(
        f"""
        <div class="kpi-card" style="{accent_style}">
            <div>
                <div class="kpi-header">
                    <span class="kpi-label">{label}</span>
                    {icon_html}
                </div>
                <div class="kpi-value">{value}</div>
            </div>
            {context_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_row(cards: List[Dict[str, Any]]) -> None:
    """
    Render a horizontal row of KPI cards evenly distributed.

    Each card dict accepts: label, value, context (opt), icon (opt), accent_color (opt).
    """
    if not cards:
        return
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        with col:
            render_kpi_card(
                label=card.get("label", ""),
                value=str(card.get("value", "—")),
                context=card.get("context", ""),
                icon=card.get("icon", ""),
                accent_color=card.get("accent_color", ""),
            )


# ---------------------------------------------------------------------------
# Status Badges
# ---------------------------------------------------------------------------

_BADGE_MAP = {
    # Risk Levels
    "low":          ("badge-low",          "LOW RISK"),
    "moderate":     ("badge-moderate",     "MODERATE RISK"),
    "high":         ("badge-high",         "HIGH RISK"),
    "critical":     ("badge-critical",     "CRITICAL RISK"),
    # Recovery Pipeline
    "detected":     ("badge-detected",     "DETECTED"),
    "disputed":     ("badge-disputed",     "DISPUTED"),
    "under review": ("badge-review",       "UNDER REVIEW"),
    "under_review": ("badge-review",       "UNDER REVIEW"),
    "recovered":    ("badge-recovered",    "RECOVERED"),
    "rejected":     ("badge-rejected",     "REJECTED"),
    # Audit & Finding Statuses
    "open":         ("badge-open",         "OPEN"),
    "resolved":     ("badge-resolved",     "RESOLVED"),
    "closed":       ("badge-closed",       "CLOSED"),
    # Document Statuses
    "ready":        ("badge-success",      "READY"),
    "processing":   ("badge-moderate",     "PROCESSING"),
    "uploaded":     ("badge-open",         "UPLOADED"),
    "error":        ("badge-critical",     "ERROR"),
    # Generic & Dispute States
    "success":      ("badge-success",      "SUCCESS"),
    "active":       ("badge-success",      "ACTIVE"),
    "inactive":     ("badge-closed",       "INACTIVE"),
    "draft":        ("badge-neutral",      "DRAFT"),
    "submitted":    ("badge-moderate",     "SUBMITTED"),
    "accepted":     ("badge-success",      "ACCEPTED"),
}


def render_status_badge(status: str, custom_label: str = "") -> str:
    """Return an HTML snippet for a styled status badge."""
    key = (status or "").lower().strip()
    css_class, default_label = _BADGE_MAP.get(
        key,
        ("badge-neutral", status.upper() if status else "UNKNOWN")
    )
    label = custom_label or default_label
    return f'<span class="status-badge {css_class}">{label}</span>'


def render_status_badge_inline(status: str, custom_label: str = "") -> None:
    """Render a status badge directly via Streamlit markdown."""
    st.markdown(render_status_badge(status, custom_label), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Empty States
# ---------------------------------------------------------------------------

def render_empty_state(
    title: str,
    description: str = "",
    icon: str = "📁",
) -> None:
    """Render a clear, intentional empty state card."""
    desc_html = f'<p class="empty-state-desc">{description}</p>' if description else ""
    st.markdown(
        f"""
        <div class="empty-state-box">
            <span class="empty-state-icon">{icon}</span>
            <h4 class="empty-state-title">{title}</h4>
            {desc_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Finding Cards
# ---------------------------------------------------------------------------

def render_finding_card(
    category: str,
    title: str,
    description: str,
    severity: str,
    billed: float = 0.0,
    allowed: float = 0.0,
    recovery: float = 0.0,
    evidence: str = "",
    property_name: str = "",
) -> None:
    """
    Render a polished financial finding card with distinct comparison grid.

    Distinguishes Billed, Allowed, and Potential Recovery with clear contrast.
    """
    sev_key = (severity or "low").lower()
    sev_badge = render_status_badge(sev_key)
    prop_html = f'<span class="finding-property">Property: <strong>{property_name}</strong></span>' if property_name else ""

    evidence_html = (
        f"""
        <div style="margin-top:0.75rem;">
            <span style="font-size:0.6875rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.04em; display:block; margin-bottom:0.25rem;">
                Contract Evidence
            </span>
            <div class="finding-evidence-box">"{evidence}"</div>
        </div>
        """
        if evidence else ""
    )

    amounts_html = ""
    if billed or allowed or recovery:
        amounts_html = f"""
        <div class="finding-amounts-grid">
            <div class="finding-amount-col">
                <span class="finding-amount-lbl">Billed Amount</span>
                <span class="finding-amount-val">{format_currency(billed)}</span>
            </div>
            <div class="finding-amount-col">
                <span class="finding-amount-lbl">Contract Allowed</span>
                <span class="finding-amount-val">{format_currency(allowed)}</span>
            </div>
            <div class="finding-amount-col recovery-col">
                <span class="finding-amount-lbl">Potential Recovery</span>
                <span class="finding-amount-val recovery-val">{format_currency(recovery)}</span>
            </div>
        </div>
        """

    st.markdown(
        f"""
        <div class="finding-card finding-{sev_key}">
            <div class="finding-header">
                <div>
                    {sev_badge}
                    <span class="finding-category-tag">{category.upper()}</span>
                </div>
                {prop_html}
            </div>
            <div class="finding-title">{title}</div>
            <div class="finding-description">{description}</div>
            {amounts_html}
            {evidence_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Visual Stepper
# ---------------------------------------------------------------------------

def render_stepper(steps: List[str], current_index: int) -> None:
    """
    Render a horizontal multi-step progress bar.

    Args:
        steps: List of step titles (e.g. ['Select Property', 'Lease Terms', ...])
        current_index: 0-based active step index
    """
    items_html = []
    for idx, step_name in enumerate(steps):
        state_class = "done" if idx < current_index else ("active" if idx == current_index else "")
        circle_content = "✓" if idx < current_index else f"{idx + 1:02d}"
        items_html.append(
            f"""
            <div class="stepper-item {state_class}">
                <div class="stepper-circle">{circle_content}</div>
                <div class="stepper-text">
                    <span class="stepper-step-num">Step {idx + 1:02d}</span>
                    <span class="stepper-title">{step_name}</span>
                </div>
            </div>
            """
        )

    st.markdown(
        f'<div class="stepper-wrapper">{"".join(items_html)}</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Alert Banners
# ---------------------------------------------------------------------------

def render_alert(message: str, kind: str = "info", title: str = "") -> None:
    """
    Render a compact, styled enterprise alert banner.

    Args:
        message: Body text
        kind: 'info' | 'success' | 'warning' | 'error'
        title: Optional bold header line
    """
    css_class = f"alert-{kind}"
    title_html = f"<strong>{title}</strong><br>" if title else ""
    st.markdown(
        f'<div class="alert-box {css_class}">{title_html}{message}</div>',
        unsafe_allow_html=True,
    )


def render_divider(spacing: str = "1.25rem") -> None:
    """Render a clean subtle horizontal separator."""
    st.markdown(
        f'<div style="border-top: 1px solid #E2E8F0; margin: {spacing} 0;"></div>',
        unsafe_allow_html=True,
    )
