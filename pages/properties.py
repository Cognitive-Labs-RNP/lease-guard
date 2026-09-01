"""
Properties page for LeaseGuard.

Manage and review all properties with risk and audit details.
"""

from typing import Any, Dict, Optional

import streamlit as st

from services.auth import get_supabase_client, require_current_user_id
from ui.custom_theme import COLORS, get_color


def _get_properties() -> list[Dict[str, Any]]:
    """Fetch user's properties."""
    user_id = require_current_user_id()
    client = get_supabase_client()

    response = client.table("properties").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return response.data or []


def _get_property_detail(prop_id: str) -> Optional[Dict[str, Any]]:
    """Fetch detailed property info."""
    client = get_supabase_client()
    response = client.table("properties").select("*").eq("id", prop_id).execute()
    return (response.data or [None])[0]


def _get_property_risk_score(prop_id: str) -> Optional[Dict[str, Any]]:
    """Fetch risk score for property."""
    client = get_supabase_client()
    response = (
        client.table("risk_scores")
        .select("overall_score, risk_level, score_breakdown")
        .eq("property_id", prop_id)
        .order("calculated_at", desc=True)
        .limit(1)
        .execute()
    )
    return (response.data or [None])[0]


def _get_property_audits(prop_id: str) -> list[Dict[str, Any]]:
    """Fetch audits for property."""
    client = get_supabase_client()
    response = (
        client.table("audits")
        .select("*")
        .eq("property_id", prop_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def _get_property_findings(prop_id: str) -> list[Dict[str, Any]]:
    """Fetch findings for property."""
    client = get_supabase_client()
    response = (
        client.table("findings")
        .select("*")
        .eq("property_id", prop_id)
        .order("severity", desc=True)
        .execute()
    )
    return response.data or []


def _get_property_recovery(prop_id: str) -> list[Dict[str, Any]]:
    """Fetch recovery records for property."""
    client = get_supabase_client()
    response = (
        client.table("recovery_records")
        .select("*")
        .eq("property_id", prop_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def _create_property(name: str, address: str, city: str, state: str, postal_code: str, country: str, prop_type: str):
    """Create a new property."""
    user_id = require_current_user_id()
    client = get_supabase_client()

    response = client.table("properties").insert({
        "user_id": user_id,
        "name": name,
        "address": address,
        "city": city,
        "state": state,
        "postal_code": postal_code,
        "country": country,
        "property_type": prop_type,
        "status": "active",
    }).execute()

    return response.data or []


def render():
    """Render the properties page."""
    st.markdown("## 🏢 Properties")

    tab1, tab2 = st.tabs(["All Properties", "Add Property"])

    with tab1:
        properties = _get_properties()

        if not properties:
            st.info("No properties yet. Create one to get started!")
        else:
            # Quick stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Properties", len(properties))
            with col2:
                active = sum(1 for p in properties if p.get("status") == "active")
                st.metric("Active", active)
            with col3:
                inactive = sum(1 for p in properties if p.get("status") != "active")
                st.metric("Inactive", inactive)

            st.markdown("### Property List")

            # Property selection
            prop_names = [p["name"] for p in properties]
            selected_name = st.selectbox("Select property", prop_names, key="prop_list")

            selected_prop = next((p for p in properties if p["name"] == selected_name), None)

            if selected_prop:
                st.markdown("---")
                st.markdown(f"### {selected_prop['name']}")

                # Property info
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Address**: {selected_prop.get('address', 'N/A')}")
                    st.write(f"**City**: {selected_prop.get('city', 'N/A')}")
                    st.write(f"**State**: {selected_prop.get('state', 'N/A')}")

                with col2:
                    st.write(f"**Postal Code**: {selected_prop.get('postal_code', 'N/A')}")
                    st.write(f"**Country**: {selected_prop.get('country', 'N/A')}")
                    st.write(f"**Type**: {selected_prop.get('property_type', 'N/A')}")
                    st.write(f"**Status**: {selected_prop.get('status', 'N/A')}")

                # Risk score
                risk = _get_property_risk_score(selected_prop["id"])
                if risk:
                    st.markdown("### Risk Assessment")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Risk Score", f"{risk.get('overall_score', 0)}/100")
                    with col2:
                        st.write(f"**Risk Level**: {risk.get('risk_level', 'N/A')}")
                    with col3:
                        pass  # Placeholder

                # Audits
                st.markdown("### Recent Audits")
                audits = _get_property_audits(selected_prop["id"])
                if audits:
                    for audit in audits[:5]:
                        with st.container(border=True):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.write(f"**Type**: {audit.get('audit_type', 'N/A')}")
                            with col2:
                                st.write(f"**Status**: {audit.get('status', 'N/A')}")
                            with col3:
                                st.write(f"**Date**: {audit.get('created_at', 'N/A')[:10]}")
                else:
                    st.info("No audits yet")

                # Findings
                st.markdown("### Findings")
                findings = _get_property_findings(selected_prop["id"])
                if findings:
                    for finding in findings[:10]:
                        with st.container(border=True):
                            col1, col2, col3 = st.columns([2, 1, 1])
                            with col1:
                                st.write(f"**{finding.get('category', 'N/A')}**: {finding.get('description', 'N/A')}")
                            with col2:
                                st.write(f"Severity: {finding.get('severity', 'N/A')}")
                            with col3:
                                st.write(f"${float(finding.get('amount', 0)):,.2f}")
                else:
                    st.info("No findings yet")

                # Recovery
                st.markdown("### Recovery Records")
                recovery = _get_property_recovery(selected_prop["id"])
                if recovery:
                    for rec in recovery[:10]:
                        with st.container(border=True):
                            col1, col2, col3 = st.columns([2, 1, 1])
                            with col1:
                                st.write(f"**Status**: {rec.get('status', 'N/A')}")
                            with col2:
                                st.write(f"**Amount**: ${float(rec.get('amount', 0)):,.2f}")
                            with col3:
                                st.write(f"**Date**: {rec.get('created_at', 'N/A')[:10]}")
                else:
                    st.info("No recovery records yet")

    with tab2:
        st.markdown("### Create New Property")
        with st.form("create_property_form"):
            name = st.text_input("Property Name*", placeholder="e.g., Downtown Office Tower")
            address = st.text_input("Address", placeholder="123 Main St")
            city = st.text_input("City", placeholder="New York")
            state = st.text_input("State", placeholder="NY")
            postal_code = st.text_input("Postal Code", placeholder="10001")
            country = st.text_input("Country", placeholder="USA", value="USA")
            prop_type = st.selectbox("Property Type", ["Office", "Retail", "Industrial", "Multifamily", "Other"])

            submitted = st.form_submit_button("Create Property")

            if submitted:
                if name.strip():
                    try:
                        _create_property(name, address, city, state, postal_code, country, prop_type)
                        st.success("Property created successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating property: {str(e)}")
                else:
                    st.error("Property name is required")
