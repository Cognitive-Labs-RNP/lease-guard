import os
from typing import Any, Dict, Optional

import streamlit as st
from dotenv import load_dotenv
from supabase import Client, create_client

from services.demo import get_demo_client, get_demo_user_id, is_demo_mode

load_dotenv()


def _get_supabase_url() -> str:
    return os.getenv("SUPABASE_URL", "").strip()


def _get_supabase_key() -> str:
    return os.getenv("SUPABASE_KEY", "").strip()


def get_supabase_client() -> Client:
    if is_demo_mode():
        # Demo Mode is an explicit, local-only workflow. It must not require
        # credentials or accidentally write sample data to a real project.
        return get_demo_client()  # type: ignore[return-value]
    url = _get_supabase_url()
    key = _get_supabase_key()

    if not url or not key:
        raise ValueError(
            "Supabase configuration is missing. Add SUPABASE_URL and SUPABASE_KEY to your environment."
        )

    return create_client(url, key)


def register_user(email: str, password: str) -> Dict[str, Any]:
    email = (email or "").strip()
    password = password or ""

    if not email or not password:
        return {"success": False, "message": "Email and password are required."}

    try:
        client = get_supabase_client()
        response = client.auth.sign_up({"email": email, "password": password})

        if getattr(response, "user", None):
            return {"success": True, "message": "Registration successful. Please sign in."}

        return {"success": False, "message": "Registration could not be completed."}
    except Exception as exc:  # pragma: no cover - failure path for runtime usage
        return {"success": False, "message": str(exc)}


def login_user(email: str, password: str) -> Dict[str, Any]:
    email = (email or "").strip()
    password = password or ""

    if not email or not password:
        return {"success": False, "message": "Email and password are required."}

    try:
        client = get_supabase_client()
        response = client.auth.sign_in_with_password({"email": email, "password": password})
        session = getattr(response, "session", None)

        if session is not None:
            st.session_state["supabase_access_token"] = session.access_token
            st.session_state["supabase_refresh_token"] = session.refresh_token
            st.session_state["supabase_user"] = response.user
            return {"success": True, "message": "Login successful."}

        return {"success": False, "message": "Login failed. Please check your credentials."}
    except Exception as exc:  # pragma: no cover - failure path for runtime usage
        return {"success": False, "message": str(exc)}


def logout_user() -> None:
    if is_demo_mode():
        return
    try:
        client = get_supabase_client()
        client.auth.sign_out()
    except Exception:
        pass

    st.session_state.pop("supabase_user", None)
    st.session_state.pop("supabase_access_token", None)
    st.session_state.pop("supabase_refresh_token", None)


def get_current_user() -> Optional[Dict[str, Any]]:
    if is_demo_mode():
        return {"id": get_demo_user_id(), "email": "demo@leaseguard.local"}
    user = st.session_state.get("supabase_user")
    if user is not None:
        return user

    access_token = st.session_state.get("supabase_access_token")
    refresh_token = st.session_state.get("supabase_refresh_token")

    if not access_token or not refresh_token:
        return None

    try:
        client = get_supabase_client()
        client.auth.set_session(access_token, refresh_token)
        response = client.auth.get_user()
        current_user = getattr(response, "user", None)

        if current_user is None:
            logout_user()
            return None

        st.session_state["supabase_user"] = current_user
        return current_user
    except Exception:
        logout_user()
        return None


def get_current_user_id() -> Optional[str]:
    user = get_current_user()
    if user is None:
        return None

    if isinstance(user, dict):
        return user.get("id")

    user_id = getattr(user, "id", None)
    return str(user_id) if user_id is not None else None


def require_current_user_id() -> str:
    user_id = get_current_user_id()
    if not user_id:
        raise ValueError("An authenticated user is required for this action.")
    return user_id
