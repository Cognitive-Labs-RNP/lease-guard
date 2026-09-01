"""
Demo mode service.

Provides realistic sample data for demonstration without external dependencies.
All demo data is clearly labeled as DEMO DATA.
"""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List
from uuid import NAMESPACE_URL, uuid5

from dotenv import load_dotenv

load_dotenv()


def is_demo_mode() -> bool:
    """Check if demo mode is enabled via DEMO_MODE env var."""
    return os.getenv("DEMO_MODE", "false").lower() == "true"


def get_demo_user_id() -> str:
    """Get demo user ID for demo mode."""
    # Stable IDs make the demo repeatable across reruns.
    return "00000000-0000-0000-0000-000000000001"


def _demo_id(name: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"leaseguard-demo/{name}"))


def get_demo_properties() -> List[Dict[str, Any]]:
    """Get sample properties for demo."""
    user_id = get_demo_user_id()
    now = datetime.now()

    return [
        {
            "id": _demo_id("property/downtown"),
            "user_id": user_id,
            "name": "Downtown Office Plaza",
            "address": "123 Main Street",
            "city": "San Francisco",
            "state": "CA",
            "postal_code": "94105",
            "country": "USA",
            "property_type": "Office",
            "status": "active",
            "created_at": (now - timedelta(days=90)).isoformat(),
            "updated_at": now.isoformat(),
        },
        {
            "id": _demo_id("property/retail"),
            "user_id": user_id,
            "name": "Retail Shopping Center",
            "address": "456 Oak Avenue",
            "city": "Austin",
            "state": "TX",
            "postal_code": "78701",
            "country": "USA",
            "property_type": "Retail",
            "status": "active",
            "created_at": (now - timedelta(days=60)).isoformat(),
            "updated_at": now.isoformat(),
        },
        {
            "id": _demo_id("property/industrial"),
            "user_id": user_id,
            "name": "Industrial Warehouse",
            "address": "789 Commerce Drive",
            "city": "Dallas",
            "state": "TX",
            "postal_code": "75201",
            "country": "USA",
            "property_type": "Industrial",
            "status": "active",
            "created_at": (now - timedelta(days=30)).isoformat(),
            "updated_at": now.isoformat(),
        },
    ]


def get_demo_audits(properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get sample audits for demo."""
    audits = []
    now = datetime.now()

    for i, prop in enumerate(properties):
        audits.append({
            "id": _demo_id(f"audit/{i}"),
            "user_id": prop["user_id"],
            "property_id": prop["id"],
            "audit_type": "Manual Entry",
            "status": "completed",
            "total_findings": 3 + i,
            "total_invoice_amount": 45000 + (i * 10000),
            "created_at": (now - timedelta(days=45 - i * 10)).isoformat(),
            "updated_at": (now - timedelta(days=45 - i * 10)).isoformat(),
            "notes": f"[DEMO] Sample audit #{i+1} for {prop['name']}",
        })

    return audits


def get_demo_findings(properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get sample findings for demo."""
    findings = []
    now = datetime.now()
    severities = ["Critical", "High", "Medium", "Low"]
    categories = ["CAM cap", "Rent escalation", "Administrative fee", "Tax pass-through", "Audit rights"]

    prop_idx = 0
    for finding_idx in range(12):
        prop = properties[prop_idx % len(properties)]
        severity = severities[finding_idx % len(severities)]

        findings.append({
            "id": _demo_id(f"finding/{finding_idx}"),
            "user_id": prop["user_id"],
            "property_id": prop["id"],
            "audit_id": _demo_id(f"audit/{prop_idx % len(properties)}"),
            "category": categories[finding_idx % len(categories)],
            "severity": severity,
            "title": f"[DEMO] {categories[finding_idx % len(categories)]} Issue #{finding_idx + 1}",
            "description": f"Sample finding: {categories[finding_idx % len(categories)]} overcharge detected",
            "amount": 1000 + (finding_idx * 200),
            "status": "open" if finding_idx % 3 == 0 else "under_review",
            "created_at": (now - timedelta(days=40 - finding_idx)).isoformat(),
            "updated_at": (now - timedelta(days=40 - finding_idx)).isoformat(),
        })
        if (finding_idx + 1) % 4 == 0:
            prop_idx += 1

    return findings


def get_demo_risk_scores(properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get sample risk scores for demo."""
    scores = []
    now = datetime.now()

    risk_levels = ["Critical", "High", "Moderate", "Low"]

    for i, prop in enumerate(properties):
        overall_score = 75 - (i * 20)  # Decreasing risk across properties

        scores.append({
            "id": _demo_id(f"risk/{i}"),
            "user_id": prop["user_id"],
            "property_id": prop["id"],
            "overall_score": overall_score,
            "risk_level": "high" if overall_score >= 60 else "moderate" if overall_score >= 35 else "low",
            "score_breakdown": {"CAM risk": 60 + (i * 10), "Rent escalation risk": 50 + (i * 5), "Administrative fee risk": 40 + (i * 5), "Tax risk": 30, "Audit rights risk": 35 + (i * 5)},
            "calculated_at": (now - timedelta(days=30 - i * 5)).isoformat(),
            "notes": f"[DEMO] Sample risk assessment for {prop['name']}",
        })

    return scores


def get_demo_recovery_records(properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get sample recovery records for demo."""
    records = []
    now = datetime.now()
    statuses = ["Detected", "Disputed", "Under Review", "Recovered", "Rejected"]

    for i in range(10):
        prop = properties[i % len(properties)]
        status_idx = i % len(statuses)

        records.append({
            "id": _demo_id(f"recovery/{i}"),
            "user_id": prop["user_id"],
            "property_id": prop["id"],
            "finding_id": None,
            "status": statuses[status_idx],
            "amount": 5000 + (i * 500),
            "created_at": (now - timedelta(days=35 - i * 3)).isoformat(),
            "updated_at": (now - timedelta(days=35 - i * 3)).isoformat(),
            "notes": f"[DEMO] Recovery record #{i + 1} - {statuses[status_idx]}",
        })

    return records


def get_demo_disputes(properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get sample disputes for demo."""
    disputes = []
    now = datetime.now()
    statuses = ["Draft", "Submitted", "Under Review", "Accepted", "Rejected"]

    for i in range(6):
        prop = properties[i % len(properties)]
        status_idx = i % len(statuses)

        disputes.append({
            "id": _demo_id(f"dispute/{i}"),
            "user_id": prop["user_id"],
            "property_id": prop["id"],
            "recovery_record_id": _demo_id(f"recovery/{i % 10}"),
            "title": f"[DEMO] Dispute #{i + 1} - {prop['name']}",
            "summary": f"Dispute regarding overcharged CAM expenses for {prop['name']}. "
                      f"Tenant was billed beyond contractual limits.",
            "status": statuses[status_idx],
            "created_at": (now - timedelta(days=25 - i * 3)).isoformat(),
            "updated_at": (now - timedelta(days=25 - i * 3)).isoformat(),
        })

    return disputes


def get_demo_documents(properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get sample documents for demo."""
    from services.extraction import get_sample_invoice_data, get_sample_lease_data

    documents = []
    now = datetime.now()
    types = ["Lease", "Invoice"]

    for i, prop in enumerate(properties):
        for j, doc_type in enumerate(types):
            documents.append({
            "id": _demo_id(f"document/{i}/{doc_type.lower()}"),
                "user_id": prop["user_id"],
                "property_id": prop["id"],
                "document_type": doc_type,
                "file_name": f"[DEMO] {prop['name']} {doc_type}.pdf",
                "storage_path": f"demo/{prop['id']}/{doc_type}/sample.pdf",
                "document_status": "ready" if i % 2 == 0 else "uploaded",
                "metadata": {
                    "demo": True,
                    "pages": 15 + (i * 5),
                    "extraction_attempted": True,
                    "extraction_status": "success",
                    "extraction_confidence": 1.0,
                    "extracted_data": get_sample_lease_data() if doc_type == "Lease" else get_sample_invoice_data(),
                },
                "created_at": (now - timedelta(days=50 - i * 10 - j * 3)).isoformat(),
                "updated_at": (now - timedelta(days=50 - i * 10 - j * 3)).isoformat(),
            })

    return documents


def apply_demo_data(client) -> Dict[str, int]:
    """
    Apply demo data to Supabase.

    Clears existing tables and inserts demo data.
    Returns count of inserted records per table.

    Args:
        client: Supabase client

    Returns:
        Dict with insertion counts per table
    """
    results = {}

    # Get demo data
    properties = get_demo_properties()
    audits = get_demo_audits(properties)
    findings = get_demo_findings(properties)
    risk_scores = get_demo_risk_scores(properties)
    recovery_records = get_demo_recovery_records(properties)
    disputes = get_demo_disputes(properties)
    documents = get_demo_documents(properties)

    # Insert data
    try:
        user_id = properties[0]["user_id"] if properties else "demo-user"

        # Insert properties
        client.table("properties").insert(properties).execute()
        results["properties"] = len(properties)

        # Insert audits
        if audits:
            client.table("audits").insert(audits).execute()
            results["audits"] = len(audits)

        # Insert findings
        if findings:
            client.table("findings").insert(findings).execute()
            results["findings"] = len(findings)

        # Insert risk scores
        if risk_scores:
            client.table("risk_scores").insert(risk_scores).execute()
            results["risk_scores"] = len(risk_scores)

        # Insert recovery records
        if recovery_records:
            client.table("recovery_records").insert(recovery_records).execute()
            results["recovery_records"] = len(recovery_records)

        # Insert disputes
        if disputes:
            client.table("disputes").insert(disputes).execute()
            results["disputes"] = len(disputes)

        # Insert documents
        if documents:
            client.table("documents").insert(documents).execute()
            results["documents"] = len(documents)

    except Exception as e:
        raise RuntimeError(f"Failed to load demo data: {str(e)}")

    return results


class _DemoResponse:
    def __init__(self, data: List[Dict[str, Any]], count: int | None = None) -> None:
        self.data = data
        self.count = len(data) if count is None else count


class _DemoTable:
    """A small, in-memory subset of the Supabase query interface for Demo Mode."""

    def __init__(self, store: Dict[str, List[Dict[str, Any]]], name: str) -> None:
        self.store, self.name = store, name
        self.filters: List[tuple[str, Any, str]] = []
        self._order: tuple[str, bool] | None = None
        self._limit: int | None = None
        self._operation = "select"
        self._payload: Any = None

    def select(self, *_args: Any, **_kwargs: Any) -> "_DemoTable":
        return self

    def eq(self, field: str, value: Any) -> "_DemoTable":
        self.filters.append((field, value, "eq"))
        return self

    def gte(self, field: str, value: Any) -> "_DemoTable":
        self.filters.append((field, value, "gte"))
        return self

    def order(self, field: str, desc: bool = False) -> "_DemoTable":
        self._order = (field, desc)
        return self

    def limit(self, value: int) -> "_DemoTable":
        self._limit = value
        return self

    def insert(self, payload: Any) -> "_DemoTable":
        self._operation, self._payload = "insert", payload
        return self

    def update(self, payload: Dict[str, Any]) -> "_DemoTable":
        self._operation, self._payload = "update", payload
        return self

    def delete(self) -> "_DemoTable":
        self._operation = "delete"
        return self

    def _matching(self) -> List[Dict[str, Any]]:
        rows = self.store.setdefault(self.name, [])
        matched = list(rows)
        for field, value, operation in self.filters:
            if operation == "eq":
                matched = [row for row in matched if row.get(field) == value]
            else:
                matched = [row for row in matched if row.get(field, 0) >= value]
        return matched

    def execute(self) -> _DemoResponse:
        rows = self.store.setdefault(self.name, [])
        matched = self._matching()
        if self._operation == "insert":
            payloads = self._payload if isinstance(self._payload, list) else [self._payload]
            created = []
            for payload in payloads:
                row = dict(payload)
                row.setdefault("id", _demo_id(f"{self.name}/added/{len(rows)}"))
                row.setdefault("created_at", datetime.now().isoformat())
                rows.append(row)
                created.append(row)
            return _DemoResponse(created)
        if self._operation == "update":
            for row in matched:
                row.update(self._payload)
                row["updated_at"] = datetime.now().isoformat()
            return _DemoResponse(matched)
        if self._operation == "delete":
            self.store[self.name] = [row for row in rows if row not in matched]
            return _DemoResponse(matched)
        if self._order:
            field, descending = self._order
            matched.sort(key=lambda row: (row.get(field) is None, row.get(field)), reverse=descending)
        if self._limit is not None:
            matched = matched[:self._limit]
        return _DemoResponse(matched)


class DemoSupabaseClient:
    """Explicit local-only storage used when DEMO_MODE=true; it never contacts Supabase."""

    def __init__(self) -> None:
        properties = get_demo_properties()
        self.store = {
            "properties": properties,
            "audits": get_demo_audits(properties),
            "findings": get_demo_findings(properties),
            "risk_scores": get_demo_risk_scores(properties),
            "recovery_records": get_demo_recovery_records(properties),
            "disputes": get_demo_disputes(properties),
            "documents": get_demo_documents(properties),
        }

    def table(self, name: str) -> _DemoTable:
        return _DemoTable(self.store, name)


_demo_client: DemoSupabaseClient | None = None


def get_demo_client() -> DemoSupabaseClient:
    """Return the process-local Demo Mode data store."""
    global _demo_client
    if _demo_client is None:
        _demo_client = DemoSupabaseClient()
    return _demo_client
