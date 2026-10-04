from decimal import Decimal, InvalidOperation

from src.config import (
    EXPECTED_PAYMENT_RECIPIENT,
    UNLOCK_PRICE,
)


SUCCESS_STATUSES = {
    "successful",
    "success",
    "completed",
    "complete",
    "paid",
    "sent",
}


def _normalize_text(value):
    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .lower()
    )


def _normalize_amount(value):

    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return None

    try:

        text = str(value)

        text = (
            text
            .replace(
                "rs.",
                "",
            )
            .replace(
                "rs",
                "",
            )
            .replace(
                "pkr",
                "",
            )
            .replace(
                ",",
                "",
            )
            .strip()
        )

        return Decimal(text)

    except (
        InvalidOperation,
        ValueError,
        TypeError,
    ):

        return None


def verify_payment(payment_data):
    """
    Deterministic demo payment validation.

    Vision AI may extract the fields, but it does NOT
    decide whether payment is valid.

    The application checks:
    recipient
    amount
    status
    """

    if not isinstance(
        payment_data,
        dict,
    ):

        return {
            "verified": False,
            "reason": "Invalid payment data.",
        }


    recipient = _normalize_text(
        payment_data.get(
            "recipient",
            "",
        )
    )

    status = _normalize_text(
        payment_data.get(
            "status",
            "",
        )
    )

    amount = _normalize_amount(
        payment_data.get(
            "amount",
            None,
        )
    )

    expected_recipient = (
        _normalize_text(
            EXPECTED_PAYMENT_RECIPIENT
        )
    )

    expected_amount = Decimal(
        str(UNLOCK_PRICE)
    )


    recipient_ok = (
        bool(recipient)
        and bool(expected_recipient)
        and (
            recipient
            == expected_recipient
            or expected_recipient
            in recipient
        )
    )


    amount_ok = (
        amount is not None
        and amount == expected_amount
    )


    status_ok = (
        status in SUCCESS_STATUSES
    )


    verified = (
        recipient_ok
        and amount_ok
        and status_ok
    )


    reasons = []

    if not recipient_ok:
        reasons.append(
            "Recipient does not match the expected demo recipient."
        )

    if not amount_ok:
        reasons.append(
            f"Amount must be Rs. {UNLOCK_PRICE}."
        )

    if not status_ok:
        reasons.append(
            "Payment status was not recognized as successful."
        )


    return {
        "verified": verified,
        "recipient_ok": recipient_ok,
        "amount_ok": amount_ok,
        "status_ok": status_ok,
        "expected_recipient": (
            EXPECTED_PAYMENT_RECIPIENT
        ),
        "expected_amount": UNLOCK_PRICE,
        "reason": (
            "Payment passed all deterministic checks."
            if verified
            else " ".join(reasons)
        ),
    }
