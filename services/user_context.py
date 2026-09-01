from typing import Any, Dict, Optional

from services.auth import get_current_user_id, get_supabase_client


def get_authenticated_user_id() -> Optional[str]:
    return get_current_user_id()


def require_authenticated_user_id() -> str:
    user_id = get_current_user_id()
    if not user_id:
        raise ValueError("A logged-in user is required to perform this action.")
    return user_id


def create_property(property_data: Dict[str, Any]) -> Dict[str, Any]:
    user_id = require_authenticated_user_id()
    client = get_supabase_client()

    payload = dict(property_data)
    payload["user_id"] = user_id

    response = client.table("properties").insert(payload).execute()
    if hasattr(response, "data"):
        return {"success": True, "data": response.data}
    return {"success": False, "message": "Property could not be created."}


def get_user_properties() -> Dict[str, Any]:
    user_id = require_authenticated_user_id()
    client = get_supabase_client()

    response = client.table("properties").select("*").eq("user_id", user_id).execute()
    if hasattr(response, "data"):
        return {"success": True, "data": response.data}
    return {"success": False, "message": "Could not load properties."}
