"""
LeaseGuard AI — Enterprise Lease Audit Platform

Main application entry point.
Handles:
  - Theme injection
  - Authentication boundary (isolated auth view, ZERO sidebar/navigation when logged out)
  - Protected enterprise shell (Dark Navy sidebar + Light Workspace)
  - Routing to all 10 application pages
"""

import os
import streamlit as st
from dotenv import load_dotenv

from services.auth import get_current_user, login_user, logout_user, register_user
from services.demo import is_demo_mode
from ui.custom_theme import apply_custom_theme
from utils.ui import render_alert

load_dotenv()

st.set_page_config(
    page_title="LeaseGuard AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply global enterprise design tokens and stylesheet
apply_custom_theme()


# ---------------------------------------------------------------------------
# Authentication Screen — Completely isolated, zero sidebar or app chrome
# ---------------------------------------------------------------------------

def show_auth_screen() -> None:
    """
    Render an isolated, centered authentication screen.

    Strictly hides the sidebar and all application navigation when unauthenticated.
    """
    # Enforce strict hiding of sidebar for unauthenticated users
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"],
            [data-testid="stSidebarCollapsedControl"],
            section[data-testid="stSidebar"] {
                display: none !important;
                visibility: hidden !important;
                width: 0 !important;
            }
            .block-container {
                max-width: 900px !important;
                padding-top: 3rem !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Brand Header
    st.markdown(
        """
        <div class="auth-brand">
            <div class="auth-brand-shield">🛡️</div>
            <h1 class="auth-brand-name">LeaseGuard AI</h1>
            <p class="auth-brand-tagline">AI-Powered Lease Auditing &amp; Financial Recovery</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Centered Form Card (approx 440px max-width)
    left_spacer, center_card, right_spacer = st.columns([1, 2.2, 1])

    with center_card:
        st.markdown('<div class="auth-card-container">', unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["Sign In", "Create Account"])

        # ----- Sign In Tab -----
        with tab_login:
            st.markdown(
                """
                <div class="auth-card-header">
                    <h2 class="auth-card-title">Welcome back</h2>
                    <p class="auth-card-desc">Sign in to your LeaseGuard workspace</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("login_form", clear_on_submit=False):
                email = st.text_input(
                    "Email address",
                    placeholder="name@company.com",
                    key="login_email_input",
                )
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    key="login_password_input",
                )
                submitted = st.form_submit_button(
                    "Sign In",
                    use_container_width=True,
                    type="primary",
                )

            if submitted:
                if not email or not password:
                    render_alert("Please enter both your email address and password.", kind="error", title="Missing Credentials")
                else:
                    with st.spinner("Authenticating with LeaseGuard..."):
                        result = login_user(email, password)
                    if result.get("success"):
                        st.rerun()
                    else:
                        error_msg = result.get("message", "Unable to sign in with provided credentials.")
                        render_alert(error_msg, kind="error", title="Sign In Failed")

        # ----- Create Account Tab -----
        with tab_register:
            st.markdown(
                """
                <div class="auth-card-header">
                    <h2 class="auth-card-title">Create an account</h2>
                    <p class="auth-card-desc">Start auditing lease agreements and recovering overcharges</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("register_form", clear_on_submit=False):
                reg_email = st.text_input(
                    "Email address",
                    placeholder="name@company.com",
                    key="reg_email_input",
                )
                reg_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Minimum 8 characters",
                    key="reg_password_input",
                )
                reg_confirm = st.text_input(
                    "Confirm password",
                    type="password",
                    placeholder="Re-enter your password",
                    key="reg_confirm_input",
                )
                reg_submitted = st.form_submit_button(
                    "Create Account",
                    use_container_width=True,
                    type="primary",
                )

            if reg_submitted:
                if not reg_email or not reg_password or not reg_confirm:
                    render_alert("All fields are required to create an enterprise account.", kind="error", title="Incomplete Form")
                elif reg_password != reg_confirm:
                    render_alert("The passwords you entered do not match. Please verify and try again.", kind="error", title="Password Mismatch")
                elif len(reg_password) < 8:
                    render_alert("Your password must contain at least 8 characters.", kind="error", title="Password Too Short")
                else:
                    with st.spinner("Creating your workspace account..."):
                        result = register_user(reg_email, reg_password)
                    if result.get("success"):
                        render_alert(
                            "Account created successfully. If email confirmation is enabled, check your inbox before signing in.",
                            kind="success",
                            title="Account Created",
                        )
                    else:
                        error_msg = result.get("message", "Could not complete account creation. Please try again.")
                        render_alert(error_msg, kind="error", title="Registration Failed")

        st.markdown("</div>", unsafe_allow_html=True)

        # Footer Trust Note
        st.markdown(
            '<div class="auth-footer">🔒 Secure enterprise lease intelligence &amp; audit compliance</div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Protected Enterprise Shell — Dark Navy Sidebar + Workspace Routing
# ---------------------------------------------------------------------------

_NAV_SECTIONS = [
    ("OVERVIEW",  [("Dashboard", "◈")]),
    ("PORTFOLIO", [("Properties", "🏢"), ("Documents", "📄")]),
    ("AUDIT",     [("Audits", "🔎"), ("Findings", "🔍"), ("Risk Analysis", "📊")]),
    ("RECOVERY",  [("Recovery", "💰"), ("Disputes", "⚖️")]),
    ("INSIGHTS",  [("Analytics", "📈")]),
    ("SYSTEM",    [("Settings", "⚙️")]),
]


def show_dashboard() -> None:
    """Render the protected application shell with grouped sidebar navigation."""

    with st.sidebar:
        # Brand Header in Dark Navy Sidebar
        st.markdown(
            """
            <div style="padding: 0.75rem 0.5rem 0.5rem 0.5rem;">
                <div style="display:flex; align-items:center; gap:0.75rem;">
                    <div style="width:2.25rem; height:2.25rem; border-radius:8px;
                                background:linear-gradient(135deg, #1D4ED8 0%, #0891B2 100%);
                                display:flex; align-items:center; justify-content:center;
                                font-size:1.125rem; flex-shrink:0;">
                        🛡️
                    </div>
                    <div>
                        <div style="font-size:1.0625rem; font-weight:800; color:#F8FAFC;
                                    letter-spacing:-0.025em; line-height:1.2;">
                            LeaseGuard AI
                        </div>
                        <div style="font-size:0.6875rem; color:#94A3B8; font-weight:600;
                                    letter-spacing:0.04em; text-transform:uppercase;">
                            Portfolio Intelligence
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if is_demo_mode():
            st.markdown(
                '<div class="demo-banner">🎭 DEMO MODE — Sample Data Active</div>',
                unsafe_allow_html=True,
            )

        st.divider()

        # Grouped Navigation Items
        current_page = st.session_state.get("current_page", "Dashboard")

        for group_title, items in _NAV_SECTIONS:
            st.markdown(
                f'<span class="nav-section-label">{group_title}</span>',
                unsafe_allow_html=True,
            )
            for page_name, icon in items:
                is_active = current_page == page_name
                # Display active indicator in button label
                btn_label = f"{icon}  {page_name}"
                if is_active:
                    # Highlighted active button
                    st.markdown(
                        f"""
                        <div class="sidebar-active-btn" style="margin-bottom:2px;">
                        """,
                        unsafe_allow_html=True,
                    )

                if st.button(
                    btn_label,
                    key=f"nav_btn_{page_name}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    st.session_state["current_page"] = page_name
                    st.rerun()

                if is_active:
                    st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        # Authenticated User Badge & Logout
        user = get_current_user()
        email = "Auditor"
        if user is not None:
            if isinstance(user, dict):
                email = user.get("email", "Auditor")
            else:
                email = getattr(user, "email", None) or "Auditor"

        initial = email[0].upper() if email else "U"

        st.markdown(
            f"""
            <div class="sidebar-user-card">
                <div class="sidebar-avatar">{initial}</div>
                <div style="overflow:hidden;">
                    <div class="sidebar-user-email" title="{email}">{email}</div>
                    <div class="sidebar-user-role">Enterprise Plan</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Sign Out", use_container_width=True, key="sidebar_logout_btn"):
            logout_user()
            st.session_state.pop("current_page", None)
            st.rerun()

    # -----------------------------------------------------------------------
    # Page Routing
    # -----------------------------------------------------------------------
    page = st.session_state.get("current_page", "Dashboard")

    if page == "Dashboard":
        from pages import dashboard
        dashboard.render()

    elif page == "Properties":
        from pages import properties
        properties.render()

    elif page == "Documents":
        from pages import documents
        documents.render()

    elif page == "Audits":
        from pages import audits
        audits.render()

    elif page == "Findings":
        from pages import findings
        findings.render()

    elif page == "Risk Analysis":
        from pages import risk_analysis
        risk_analysis.render()

    elif page == "Recovery":
        from pages import recovery
        recovery.render()

    elif page == "Disputes":
        from pages import disputes
        disputes.render()

    elif page == "Analytics":
        from pages import analytics
        analytics.render()

    elif page == "Settings":
        from pages import settings
        settings.render()


# ---------------------------------------------------------------------------
# Root Execution Gate
# ---------------------------------------------------------------------------

if get_current_user() is None:
    show_auth_screen()
else:
    show_dashboard()
