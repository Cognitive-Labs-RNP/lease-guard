from services.audit_engine import audit_lease_invoice
from services.recovery_engine import build_recovery_summary
from services.risk_engine import calculate_risk_score


def test_cam_overcharge() -> None:
    lease = {
        "base_rent": 10000,
        "cam_cap_pct": 0.12,
        "tenant_share_pct": 0.30,
        "excluded_expenses": ["management_fee"],
    }
    invoice = {
        "cam_expense": 4800,
        "tenant_share_pct": 0.30,
    }

    findings = audit_lease_invoice(lease, invoice)
    assert any(f["category"] == "CAM cap" and f["potential_recovery"] > 0 for f in findings)


def test_allowed_cam() -> None:
    lease = {
        "base_rent": 10000,
        "cam_cap_pct": 0.12,
        "tenant_share_pct": 0.30,
    }
    invoice = {
        "cam_expense": 250,
        "tenant_share_pct": 0.30,
    }

    findings = audit_lease_invoice(lease, invoice)
    assert not any(f["category"] == "CAM cap" for f in findings)


def test_excluded_expense() -> None:
    lease = {
        "excluded_expenses": ["management_fee"],
    }
    invoice = {
        "line_items": [
            {"category": "management_fee", "amount": 450.0},
            {"category": "utilities", "amount": 200.0},
        ]
    }

    findings = audit_lease_invoice(lease, invoice)
    assert any(f["category"] == "Excluded expense" for f in findings)


def test_rent_escalation() -> None:
    lease = {
        "base_rent": 10000,
        "annual_increase_pct": 0.05,
        "current_rent": 10000,
    }
    invoice = {
        "rent_amount": 12000,
    }

    findings = audit_lease_invoice(lease, invoice)
    assert any(f["category"] == "Rent escalation" for f in findings)


def test_recovery_calculation() -> None:
    summary = build_recovery_summary(
        [
            {"potential_recovery": 500.0},
            {"potential_recovery": 250.0},
        ],
        disputed_amount=100.0,
        amount_under_review=50.0,
        recovered_amount=0.0,
    )

    assert summary["potential_recovery"] == 750.0
    assert summary["disputed_amount"] == 100.0
    assert summary["amount_under_review"] == 50.0


def test_risk_score() -> None:
    risk = calculate_risk_score(
        {
            "cam_risk": 70,
            "rent_escalation_risk": 45,
            "administrative_fee_risk": 60,
            "tax_risk": 25,
            "audit_rights_risk": 40,
        }
    )

    assert 0 <= risk["overall_score"] <= 100
    assert risk["risk_level"] in {"low", "moderate", "high", "critical"}
    assert "CAM risk" in risk["category_scores"]
