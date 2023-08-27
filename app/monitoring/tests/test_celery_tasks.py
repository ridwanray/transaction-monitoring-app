import pytest
from django.conf import settings
from django.core import mail

pytestmark = pytest.mark.django_db

from monitoring.tasks import send_policy_email


class TestCeleryTasks:
    def test_send_policy_email(self, active_user):
        email_data = {
            "email": active_user.email,
            "message": "Random msg",
            "user_name": active_user.firstname,
        }

        send_policy_email(email_data)
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == "Policy Violation Detected"
        assert mail.outbox[0].from_email == settings.EMAIL_FROM
        assert mail.outbox[0].to[0] == active_user.email
