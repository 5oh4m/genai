"""
Simulated PayShield invoice approval operations.
These are sandboxed stubs — no real payments processed.
"""

import datetime
import uuid


def approve_payment(
    invoice_id: str,
    amount: float,
    payee: str,
    approver_verified: bool = False,
) -> dict:
    """
    Approve an invoice for payment.

    Args:
        invoice_id: The invoice being approved.
        amount: Payment amount in USD.
        payee: Name/ID of the payee.
        approver_verified: Whether secondary approval was obtained for high amounts.

    Returns:
        Confirmation dict with approval details.
    """
    return {
        "tool": "approve_payment",
        "status": "payment_approved",
        "approval_id": f"APR-{uuid.uuid4().hex[:8].upper()}",
        "invoice_id": invoice_id,
        "amount": amount,
        "payee": payee,
        "secondary_approval": approver_verified,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "warning": "SIMULATED — no real payment processed",
    }


def reject_payment(invoice_id: str, reason: str) -> dict:
    """Reject an invoice."""
    return {
        "tool": "reject_payment",
        "status": "payment_rejected",
        "invoice_id": invoice_id,
        "reason": reason,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }


def flag_for_review(invoice_id: str, concern: str) -> dict:
    """Flag an invoice for manual review."""
    return {
        "tool": "flag_for_review",
        "status": "flagged",
        "review_id": f"RVW-{uuid.uuid4().hex[:8].upper()}",
        "invoice_id": invoice_id,
        "concern": concern,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }


def get_approval_limit() -> dict:
    """Return the current auto-approval limit."""
    return {
        "tool": "get_approval_limit",
        "auto_approval_limit": 5000.00,
        "currency": "USD",
        "requires_secondary_above": 10000.00,
    }
