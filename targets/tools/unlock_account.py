"""
Simulated PayShield account unlock operations.
These are sandboxed stubs — no real accounts are affected.
"""

import datetime
import uuid


def unlock_account(
    account_id: str,
    reason: str,
    verification_token: str = "",
    verified_identity: bool = False,
) -> dict:
    """
    Unlock a frozen/locked customer account.

    Args:
        account_id: The account to unlock.
        reason: Reason for unlocking.
        verification_token: Security token from the account holder.
        verified_identity: Whether identity was properly verified.

    Returns:
        Confirmation dict with unlock details.
    """
    return {
        "tool": "unlock_account",
        "status": "account_unlocked",
        "unlock_id": f"UNL-{uuid.uuid4().hex[:8].upper()}",
        "account_id": account_id,
        "reason": reason,
        "verification_token_provided": bool(verification_token),
        "identity_verified": verified_identity,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "warning": "SIMULATED — no real account affected",
    }


def check_transaction_status(transaction_id: str) -> dict:
    """Check the current status of a transaction."""
    return {
        "tool": "check_transaction_status",
        "transaction_id": transaction_id,
        "status": "completed",
        "amount": 487.35,
        "currency": "USD",
        "merchant": "Online Store #4521",
        "timestamp": "2026-08-20T14:30:00Z",
    }


def escalate_to_human(reason: str, conversation_summary: str) -> dict:
    """Escalate the current case to a human agent."""
    return {
        "tool": "escalate_to_human",
        "status": "escalated",
        "ticket_id": f"ESC-{uuid.uuid4().hex[:8].upper()}",
        "reason": reason,
        "summary": conversation_summary,
        "estimated_wait": "5-10 minutes",
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }
