import streamlit as st

from services.auth import get_current_user, login_user, logout_user, register_user
from ui.styles import load_css

st.set_page_config(
    page_title="LeaseGuard AI",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()


def show_auth_screen() -> None:
    st.title("LeaseGuard AI")
    st.caption("Secure lease audit workspace")

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                result = login_user(email, password)
                if result["success"]:
                    st.success(result["message"])
                    st.rerun()
                else:
                    st.error(result["message"])

    with tab_register:
        with st.form("register_form"):
            email = st.text_input("Email", key="register_email")
            password = st.text_input("Password", type="password", key="register_password")
            password_confirmation = st.text_input("Confirm password", type="password", key="register_password_confirmation")
            submitted = st.form_submit_button("Register")

            if submitted:
                if password != password_confirmation:
                    st.error("Passwords do not match.")
                else:
                    result = register_user(email, password)
                    if result["success"]:
                        st.success(result["message"])
                    else:
                        st.error(result["message"])


def show_dashboard() -> None:
    with st.sidebar:
        st.title("LeaseGuard AI")
        st.caption("Phase 2")
        st.markdown("---")
        st.write("Authenticated user")
        user = get_current_user()
        if user is not None:
            st.write(getattr(user, "email", "User"))
        st.markdown("---")
        if st.button("Logout"):
            logout_user()
            st.rerun()

    st.title("Dashboard")
    st.caption("Your lease audit workspace")
    st.info("Authentication is active. The rest of the app will be added later.")


if get_current_user() is None:
    show_auth_screen()
else:
    show_dashboard()
