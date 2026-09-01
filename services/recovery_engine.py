from __future__ import annotations

from typing import Any, Dict, List


def build_recovery_summary(
    findings: List[Dict[str, Any]],
    disputed_amount: float = 0.0,
    amount_under_review: float = 0.0,
    recovered_amount: float = 0.0,
) -> Dict[str, Any]:
    potential_recovery = round(sum(float(item.get("potential_recovery", 0.0)) for item in findings), 2)
    return {
        "potential_recovery": potential_recovery,
        "disputed_amount": round(float(disputed_amount), 2),
        "amount_under_review": round(float(amount_under_review), 2),
        "recovered_amount": round(float(recovered_amount), 2),
        "status": "Detected" if potential_recovery > 0 else "Clear",
    }
