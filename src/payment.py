from typing import Any, Dict

from .config import (
    EXPECTED_PAYMENT_RECIPIENT,
    UNLOCK_PRICE,
)


def normalize_text(value: Any) -> str:
    """Normalize text for safe comparison."""
    if value is None:
        return ""

    return " ".join(str(value).strip().lower().split())


def normalize_amount(value: Any) -> float:
    """Convert common amount formats into a numeric value."""
    if value is None:
        return 0.0

    text = str(value).strip().lower()

    # Remove common currency labels and separators.
    for token in ["rs.", "rs", "pkr", "₨", "₨.", ","]:
        text = text.replace(token, "")

    text = text.strip()

    try:
        return float(text)
    except (TypeError, ValueError):
        return 0.0


def verify_payment(
    recipient: Any,
    amount: Any,
    status: Any,
) -> Dict[str, Any]:
    """
    Deterministically verify the extracted payment information.

    This is DEMO verification only.
    It does not contact JazzCash or any real payment provider.
    """

    expected_recipient = normalize_text(
        EXPECTED_PAYMENT_RECIPIENT
    )

    actual_recipient = normalize_text(recipient)

    expected_amount = float(UNLOCK_PRICE)
    actual_amount = normalize_amount(amount)

    actual_status = normalize_text(status)

    valid_statuses = {
        "sent",
        "successful",
        "completed",
    }

    recipient_match = (
        actual_recipient == expected_recipient
    )

    amount_match = (
        actual_amount == expected_amount
    )

    status_match = (
        actual_status in valid_statuses
    )

    verified = (
        recipient_match
        and amount_match
        and status_match
    )

    return {
        "verified": verified,
        "recipient": recipient,
        "amount": amount,
        "status": status,
        "expected_recipient": EXPECTED_PAYMENT_RECIPIENT,
        "expected_amount": expected_amount,
        "recipient_match": recipient_match,
        "amount_match": amount_match,
        "status_match": status_match,
        "verification_type": "AI Screenshot Verification — Demo",
    }


def verify_payment_data(
    payment_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Convenience wrapper for dictionaries returned by the Vision Agent.
    """

    if not isinstance(payment_data, dict):
        return verify_payment(
            recipient="",
            amount=0,
            status="",
        )

    return verify_payment(
        recipient=payment_data.get("recipient", ""),
        amount=payment_data.get("amount", 0),
        status=payment_data.get("status", ""),
    )


def payment_is_verified(
    recipient: Any,
    amount: Any,
    status: Any,
) -> bool:
    """Return only the final verification result."""

    result = verify_payment(
        recipient=recipient,
        amount=amount,
        status=status,
    )

    return bool(result["verified"])
