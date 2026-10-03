from typing import Any

from .config import (
    EXPECTED_PAYMENT_RECIPIENT,
    EXPECTED_PAYMENT_STATUS,
    UNLOCK_PRICE,
)


def normalize(value: Any) -> str:
    return str(value or "").strip().lower()


def validate_payment(
    vision_result: dict[str, Any]
) -> dict[str, Any]:
    """
    Deterministic demo validation.

    AI extracts the visible information.
    Python decides whether the demo conditions are satisfied.

    This does NOT verify an actual JazzCash backend transaction.
    """

    recipient = normalize(
        vision_result.get("recipient")
    )

    status = normalize(
        vision_result.get("status")
    )

    amount = vision_result.get("amount")

    try:
        amount = int(amount)
    except (TypeError, ValueError):
        amount = None

    recipient_ok = (
        recipient == EXPECTED_PAYMENT_RECIPIENT
    )

    amount_ok = (
        amount == UNLOCK_PRICE
    )

    status_ok = (
        status == EXPECTED_PAYMENT_STATUS
        or status == "successful"
        or status == "completed"
    )

    approved = (
        recipient_ok
        and amount_ok
        and status_ok
    )

    return {
        "approved": approved,
        "recipient_ok": recipient_ok,
        "amount_ok": amount_ok,
        "status_ok": status_ok,
        "recipient": recipient,
        "amount": amount,
        "status": status,
        "message": (
            "Demo screenshot conditions passed. "
            "Day 2 and Day 3 can be unlocked."
            if approved
            else
            "Screenshot conditions did not pass. "
            "Day 2 and Day 3 remain locked."
        ),
    }
