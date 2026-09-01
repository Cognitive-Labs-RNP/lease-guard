"""
Findings page for LeaseGuard AI.

Filter, inspect, and analyze lease audit discrepancies with monetary breakdowns
and contractual evidence clauses.
"""

from typing import Any, Dict, List, Optional
import streamlit as st

from services.auth import get_supabase_client, require_current_user_id
from ui.custom_theme import COLORS, get_color
from utils.ui import (
    format_currency,
    render_divider,
    render_empty_state,
    render_finding_card,
    render_kpi_card,
    render_page_header,
    render_section_header,
    render_status_badge,
)


def _get_properties() -> List[Dict[str, Any]]:
    """Fetch user's properties."""
    user_id = require_current_user_id()
    client = get_supabase_client()
    response = client.table("properties").select("id, name").eq("user_id", user_id).order("name").execute()
    return response.data or []


def _get_findings(filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Fetch findings with optional query filters."""
    user_id = require_current_user_id()
    client = get_supabase_client()

    query = client.table("findings").select("*").eq("user_id", user_id)

    if filters:
        if filters.get("property_id"):
            query = query.eq("property_id", filters["property_id"])
        if filters.get("severity"):
            query = query.eq("severity", filters["severity"])
        if filters.get("category"):
            query = query.eq("category", filters["category"])
        if filters.get("status"):
            query = query.eq("status", filters["status"])

    response = query.order("created_at", desc=True).execute()
    return response.data or []


def render():
    """Render the audit findings review page."""
    render_page_header(
        title="Audit Findings & Discrepancies",
        subtitle="Review identified lease overcharges, risk classifications, and contractual citation evidence.",
        icon="🔍",
    )

    properties = _get_properties()
    prop_dict = {p["id"]: p["name"] for p in properties}

    # -----------------------------------------------------------------------
    # Filter Bar
    # -----------------------------------------------------------------------
    with st.container(border=True):
        st.markdown("<span style='font-size:0.75rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.04em;'>Filter Discrepancies</span>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)

        prop_options = ["All Properties"] + [p["name"] for p in properties]
        with col1:
            selected_prop_name = st.selectbox("Property", prop_options, key="finding_prop_filter")
            selected_prop_id = next((p["id"] for p in properties if p["name"] == selected_prop_name), None) if selected_prop_name != "All Properties" else None

        with col2:
            severity = st.selectbox("Severity Level", ["All Severities", "critical", "high", "medium", "low"], key="finding_sev_filter")
            severity_filter = None if severity == "All Severities" else severity

        with col3:
            category = st.selectbox("Category", ["All Categories", "CAM cap", "Excluded expense", "Rent escalation", "Administrative fee", "Tenant-share calculation"], key="finding_cat_filter")
            category_filter = None if category == "All Categories" else category

        with col4:
            status = st.selectbox("Finding Status", ["All Statuses", "open", "under_review", "resolved", "closed"], key="finding_stat_filter")
            status_filter = None if status == "All Statuses" else status

    # Query findings with active filters
    filters = {
        "property_id": selected_prop_id,
        "severity": severity_filter,
        "category": category_filter,
        "status": status_filter,
    }

    findings = _get_findings(filters)

    # -----------------------------------------------------------------------
    # Severity KPI Counters
    # -----------------------------------------------------------------------
    st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

    sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    total_potential = 0.0
    for f in findings:
        s = (f.get("severity") or "low").lower()
        if s in sev_counts:
            sev_counts[s] += 1
        total_potential += float(f.get("amount", 0.0))

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        render_kpi_card("Total Discrepancies", str(len(findings)), "Matching criteria", "🔍", get_color("brand_blue"))
    with k2:
        render_kpi_card("Critical Risk", str(sev_counts["critical"]), "Immediate action", "🔴", get_color("risk_critical"))
    with k3:
        render_kpi_card("High Risk", str(sev_counts["high"]), "Significant overcharge", "🟠", get_color("risk_high"))
    with k4:
        render_kpi_card("Medium / Low", str(sev_counts["medium"] + sev_counts["low"]), "Minor variances", "🟡", get_color("risk_moderate"))
    with k5:
        render_kpi_card("Potential Recovery", format_currency(total_potential), "Sum of discrepancies", "💰", get_color("success"))

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # Findings Cards List
    # -----------------------------------------------------------------------
    render_section_header("Discrepancy Details", f"Displaying {len(findings)} matching finding record(s)")

    if findings:
        for finding in findings:
            prop_name = prop_dict.get(finding.get("property_id"), "Property")
            billed = float(finding.get("billed_amount") or finding.get("amount") or 0.0)
            allowed = float(finding.get("allowed_amount") or 0.0)
            recovery = float(finding.get("potential_recovery") or finding.get("amount") or 0.0)

            # Extract evidence
            meta = finding.get("metadata", {})
            evidence = (
                meta.get("lease_evidence", {}).get("clause", "")
                if isinstance(meta, dict) and meta.get("lease_evidence")
                else (meta.get("evidence", "") if isinstance(meta, dict) else "")
            )

            render_finding_card(
                category=finding.get("category", "Discrepancy"),
                title=finding.get("title", finding.get("category", "Lease Finding")),
                description=finding.get("description", "Discrepancy identified during lease reconciliation."),
                severity=finding.get("severity", "Medium"),
                billed=billed,
                allowed=allowed,
                recovery=recovery,
                evidence=evidence or "Pursuant to lease terms and audited expense verification.",
                property_name=prop_name,
            )
    else:
        render_empty_state(
            title="No Findings Match Selected Filters",
            description="Adjust your property, category, or severity filters above to view other recorded discrepancies.",
            icon="🔍",
        )
