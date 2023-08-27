from core.celery import APP
from django.template.loader import get_template


@APP.task()
def send_policy_email(email_data):
    from .utils import send_email

    html_template = get_template("emails/transaction_violation_template.html")
    html_alternative = html_template.render(email_data)
    send_email("Policy Violation Detected", email_data["email"], html_alternative)
