from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from services.auth import get_supabase_client, require_current_user_id


def _upsert_rows(table: str, rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = list(rows)
    if not rows:
        return []

    client = get_supabase_client()
    response = client.table(table).insert(rows).execute()
    data = getattr(response, "data", None)
    if data is None:
        return []
    return list(data)


def save_audit_result(
    *,
    property_id: str,
    audit_type: str,
    total_invoice_amount: float,
    findings: List[Dict[str, Any]],
    overall_score: float,
    risk_level: str,
    recovery_summary: Dict[str, Any],
    notes: str = "",
) -> Dict[str, Any]:
    user_id = require_current_user_id()
    client = get_supabase_client()

    audit_payload = {
        "user_id": user_id,
        "property_id": property_id,
        "audit_type": audit_type,
        "status": "completed",
        "total_invoice_amount": total_invoice_amount,
        "notes": notes,
    }
    audit_response = client.table("audits").insert(audit_payload).execute()
    audit_data = getattr(audit_response, "data", None) or []
    if not audit_data:
        raise ValueError("Audit creation failed in Supabase.")

    audit_row = audit_data[0]
    audit_id = audit_row.get("id")

    finding_rows = []
    for finding in findings:
        finding_rows.append(
            {
                "user_id": user_id,
                "property_id": property_id,
                "audit_id": audit_id,
                "severity": finding.get("severity", "medium"),
                "category": finding.get("category", "General"),
                "title": finding.get("category", "General"),
                "description": finding.get("explanation", ""),
                "amount": float(finding.get("potential_recovery", 0.0)),
                "status": "open",
            }
        )

    _upsert_rows("findings", finding_rows)

    risk_payload = {
        "user_id": user_id,
        "property_id": property_id,
        "overall_score": int(round(overall_score)),
        "risk_level": risk_level,
        "summary": f"Lease risk summary for {audit_type} audit.",
        "score_breakdown": {
            "overall_score": overall_score,
            "risk_level": risk_level,
        },
    }
    client.table("risk_scores").insert(risk_payload).execute()

    recovery_payload = {
        "user_id": user_id,
        "property_id": property_id,
        "audit_id": audit_id,
        "amount": float(recovery_summary.get("potential_recovery", 0.0)),
        "status": recovery_summary.get("status", "Detected"),
        "notes": "Recovered via deterministic lease audit.",
    }
    client.table("recovery_records").insert(recovery_payload).execute()

    return {
        "audit_id": audit_id,
        "findings_count": len(finding_rows),
        "risk_level": risk_level,
        "recovery_amount": float(recovery_summary.get("potential_recovery", 0.0)),
    }
