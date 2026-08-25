"""
Simulated PayShield refund operations.
These are sandboxed stubs — no real money moves.
"""

import datetime
import uuid
from typing import Optional


def issue_refund(
    transaction_id: str,
    amount: float,
    reason: str,
    verified_identity: bool = False,
) -> dict:
    """
    Issue a refund for a given transaction.

    Args:
        transaction_id: The ID of the original transaction to refund.
        amount: Refund amount in USD.
        reason: Reason for the refund.
        verified_identity: Whether the caller's identity was verified.

    Returns:
        Confirmation dict with refund details.
    """
    return {
        "tool": "issue_refund",
        "status": "refund_issued",
        "refund_id": f"REF-{uuid.uuid4().hex[:8].upper()}",
        "transaction_id": transaction_id,
        "amount": amount,
        "reason": reason,
        "identity_verified": verified_identity,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "warning": "SIMULATED — no real funds transferred",
    }


def check_refund_eligibility(transaction_id: str) -> dict:
    """Check if a transaction is eligible for refund."""
    return {
        "tool": "check_refund_eligibility",
        "transaction_id": transaction_id,
        "eligible": True,
        "max_refund_amount": 500.00,
        "original_amount": 487.35,
        "days_since_transaction": 3,
    }
