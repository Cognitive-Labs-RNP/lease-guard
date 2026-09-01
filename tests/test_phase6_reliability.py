import os
from unittest.mock import patch

import pytest

from services.demo import get_demo_client, get_demo_user_id
from services.extraction import _parse_extraction_response
from services.validation import validate_invoice_data


def test_demo_store_runs_without_external_configuration() -> None:
    with patch.dict(os.environ, {"DEMO_MODE": "true"}, clear=True):
        client = get_demo_client()
        properties = client.table("properties").select("*").eq("user_id", get_demo_user_id()).execute().data
        assert len(properties) == 3

        record = client.table("recovery_records").select("*").eq("user_id", get_demo_user_id()).execute().data[0]
        client.table("recovery_records").update({"status": "Disputed"}).eq("id", record["id"]).execute()
        updated = client.table("recovery_records").select("*").eq("id", record["id"]).execute().data[0]
        assert updated["status"] == "Disputed"


def test_invalid_invoice_values_are_reported_not_raised() -> None:
    valid, errors = validate_invoice_data({"cam_expense": "invalid", "rent_amount": "invalid"})
    assert not valid
    assert any("not a valid number" in error for error in errors)


def test_invoice_extraction_requires_values_needed_for_audit() -> None:
    with pytest.raises(RuntimeError, match="Missing required invoice field: rent_amount"):
        _parse_extraction_response({"result": {"answers": ['{"cam_expense": 100}']}}, "invoice")
