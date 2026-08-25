"""
Simulated PayShield merchant onboarding operations.
These are sandboxed stubs — no real merchants are onboarded.
"""

import datetime
import uuid


def approve_merchant(
    application_id: str,
    business_name: str,
    business_type: str,
    docs_verified: bool = False,
) -> dict:
    """
    Approve a merchant application for onboarding.

    Args:
        application_id: The merchant application ID.
        business_name: Name of the business.
        business_type: Category of business.
        docs_verified: Whether supporting documents were verified.

    Returns:
        Confirmation dict with approval details.
    """
    return {
        "tool": "approve_merchant",
        "status": "merchant_approved",
        "merchant_id": f"MER-{uuid.uuid4().hex[:8].upper()}",
        "application_id": application_id,
        "business_name": business_name,
        "business_type": business_type,
        "docs_verified": docs_verified,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "warning": "SIMULATED — no real merchant onboarded",
    }


def reject_merchant(application_id: str, reason: str) -> dict:
    """Reject a merchant application."""
    return {
        "tool": "reject_merchant",
        "status": "merchant_rejected",
        "application_id": application_id,
        "reason": reason,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }


def request_additional_docs(application_id: str, required_docs: list[str]) -> dict:
    """Request additional documentation from a merchant applicant."""
    return {
        "tool": "request_additional_docs",
        "status": "docs_requested",
        "request_id": f"DOC-{uuid.uuid4().hex[:8].upper()}",
        "application_id": application_id,
        "required_docs": required_docs,
        "deadline": "5 business days",
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }
