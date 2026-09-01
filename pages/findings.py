"""
Findings page for LeaseGuard.

View, filter, and analyze audit findings with evidence.
"""

from typing import Any, Dict

import pandas as pd
import streamlit as st

from services.auth import get_supabase_client, require_current_user_id
from ui.custom_theme import COLORS, get_color


def _get_findings(
    filters: Dict[str, Any] = None
) -> list[Dict[str, Any]]:
    """Fetch findings with optional filters."""
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


def _get_properties() -> list[Dict[str, Any]]:
    """Fetch user's properties."""
    user_id = require_current_user_id()
    client = get_supabase_client()
    response = client.table("properties").select("id, name").eq("user_id", user_id).order("name").execute()
    return response.data or []


def _get_finding_evidence(finding: Dict[str, Any]) -> Dict[str, Any]:
    """Extract evidence from finding."""
    return {
        "lease_evidence": finding.get("metadata", {}),
        "invoice_evidence": finding.get("metadata", {}),
    }


def render():
    """Render the findings page."""
    st.markdown("## 🔍 Findings")

    # Filters
    st.markdown("### Filters")

    col1, col2, col3, col4 = st.columns(4)

    properties = _get_properties()
    prop_dict = {p["id"]: p["name"] for p in properties}
    prop_options = ["All"] + [p["name"] for p in properties]

    with col1:
        selected_prop_name = st.selectbox("Property", prop_options, key="finding_prop")
        selected_prop_id = next((p["id"] for p in properties if p["name"] == selected_prop_name), None) if selected_prop_name != "All" else None

    with col2:
        severity = st.selectbox("Severity", ["All", "critical", "high", "medium", "low"], key="finding_severity")
        severity_filter = None if severity == "All" else severity

    with col3:
        category = st.selectbox("Category", ["All", "CAM cap", "Excluded expense", "Rent escalation", "Administrative fee", "Tenant-share calculation"], key="finding_category")
        category_filter = None if category == "All" else category

    with col4:
        status = st.selectbox("Status", ["All", "open", "under_review", "resolved", "closed"], key="finding_status")
        status_filter = None if status == "All" else status

    # Apply filters
    filters = {
        "property_id": selected_prop_id,
        "severity": severity_filter,
        "category": category_filter,
        "status": status_filter,
    }

    findings = _get_findings(filters)

    # Summary
    st.markdown("---")
    st.markdown(f"### Found {len(findings)} findings")

    if findings:
        # Statistics
        col1, col2, col3, col4 = st.columns(4)

        severity_counts = {}
        for finding in findings:
            sev = finding.get("severity", "low")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        with col1:
            critical_count = severity_counts.get("critical", 0)
            st.metric("Critical", critical_count)

        with col2:
            high_count = severity_counts.get("high", 0)
            st.metric("High", high_count)

        with col3:
            medium_count = severity_counts.get("medium", 0)
            st.metric("Medium", medium_count)

        with col4:
            low_count = severity_counts.get("low", 0)
            st.metric("Low", low_count)

        # Findings list
        st.markdown("---")

        for i, finding in enumerate(findings):
            with st.container(border=True):
                col1, col2, col3 = st.columns([1, 1, 0.5])

                with col1:
                    severity = finding.get("severity", "unknown").upper()
                    category = finding.get("category", "Unknown")
                    st.markdown(f"### {category}")
                    st.write(f"**Title**: {finding.get('title', 'N/A')}")
                    st.write(f"**Description**: {finding.get('description', 'N/A')}")

                with col2:
                    col2a, col2b = st.columns(2)
                    with col2a:
                        st.write(f"**Severity**: {severity}")
                        st.write(f"**Status**: {finding.get('status', 'N/A')}")
                    with col2b:
                        st.write(f"**Amount**: ${float(finding.get('amount', 0)):,.2f}")
                        st.write(f"**Date**: {finding.get('created_at', 'N/A')[:10]}")

                with col3:
                    if st.button("Details", key=f"detail_{finding['id']}"):
                        st.session_state[f"show_detail_{finding['id']}"] = True

                # Expandable details
                if st.session_state.get(f"show_detail_{finding['id']}", False):
                    st.markdown("---")
                    st.markdown("#### Evidence & Calculations")

                    with st.expander("Lease Evidence", expanded=False):
                        st.json(finding.get("metadata", {}))

                    with st.expander("Invoice Evidence", expanded=False):
                        st.json(finding.get("metadata", {}))

                    with st.expander("Audit Details", expanded=False):
                        audit_id = finding.get("audit_id")
                        if audit_id:
                            client = get_supabase_client()
                            audit = client.table("audits").select("*").eq("id", audit_id).execute()
                            if audit.data:
                                st.json(audit.data[0])
    else:
        st.info("No findings match the selected filters")
