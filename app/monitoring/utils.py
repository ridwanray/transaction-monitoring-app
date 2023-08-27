from typing import Any

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.defaultfilters import linebreaksbr

from .enums import TIER_AMOUNT
from .models import User

MAX_TRANSACTION_AMOUNT = 5_000_000.00 #5m


def send_email(subject: str, email_to: str, html_alternative: Any):
    msg = EmailMultiAlternatives(
        subject=subject, from_email=settings.EMAIL_FROM, to=[email_to]
    )
    msg.attach_alternative(html_alternative, "text/html")
    msg.send(fail_silently=False)


def evaluate_policy(sender: User, receiver: User, amount: float) -> dict:
    violation_message = ""
    is_flagged = False
    if receiver.is_new:
        is_flagged = True
        violation_message += "Recipient account is new.\n"
    if receiver.is_flagged:
        is_flagged = True
        violation_message += "Recipient account is flagged.\n"
    if sender.is_amount_above_tier_limit(amount):
        is_flagged = True
        violation_message += f"Transaction amount of #{amount:,} is above #{TIER_AMOUNT.get(sender.tier):,}, your tier limit.\n"
    if sender.is_within_timing_window:
        is_flagged = True
        violation_message += "Transaction violated 1 minute timing window.\n"
    if amount > MAX_TRANSACTION_AMOUNT:
        is_flagged = True
        violation_message += f"Transaction amount of #{amount:,} is above #{MAX_TRANSACTION_AMOUNT:,} max limit\n"
    violation_message = linebreaksbr(violation_message)
    return {
        "is_flagged": is_flagged,
        "violation_message": violation_message,
    }
