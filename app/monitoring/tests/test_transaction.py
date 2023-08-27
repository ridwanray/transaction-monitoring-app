from datetime import datetime, timedelta, timezone

import pytest
from django.urls import reverse
from monitoring.enums import TIER_AMOUNT
from monitoring.models import Transaction
from monitoring.utils import MAX_TRANSACTION_AMOUNT

from .conftest import api_client_with_credentials
from .factories import TransactionFactory

pytestmark = pytest.mark.django_db

SEND_POLICY_MAIL = "monitoring.tasks.send_policy_email.delay"


class TestTransaction:
    transaction_list_url = reverse("transaction:transaction-list")

    def test_make_transaction(
        self, api_client, user_factory, authenticate_user, mocker
    ):
        mock_send_policy_violation_mail = mocker.patch(SEND_POLICY_MAIL)
        recipient = user_factory()  # new user
        user = authenticate_user()
        token = user["token"]
        api_client_with_credentials(token, api_client)
        data = {"recipient": f"{recipient.id}", "amount": "200000.00"}
        response = api_client.post(self.transaction_list_url, data)
        assert response.status_code == 200
        created_transaction = Transaction.objects.get(sender=user["user_instance"])
        assert created_transaction.receiver == recipient
        assert str(created_transaction.amount) == data["amount"]
        assert created_transaction.is_flagged == True  # Recipient is a new user
        email_data = {
            "email": user.get("user_instance").email,
            "message": "Recipient account is new.<br>",
            "user_name": user.get("user_instance").firstname,
        }
        mock_send_policy_violation_mail.assert_called_once_with(email_data)

    def test_retrieve_transactions(self, api_client, user_factory, authenticate_user):
        """Retrieve transaction where authenticated user is the sender or receiver"""
        user = authenticate_user()
        TransactionFactory.create_batch(
            3, sender=user["user_instance"], receiver=user_factory()
        )
        TransactionFactory.create_batch(
            2, receiver=user["user_instance"], sender=user_factory()
        )
        TransactionFactory.create_batch(
            2, receiver=user_factory(), sender=user_factory()
        )  # Not associated to authenticated user
        token = user["token"]
        api_client_with_credentials(token, api_client)
        response = api_client.get(self.transaction_list_url)
        assert response.status_code == 200
        assert response.json()["total"] == 5

    def test_retrieve_transaction_by_id(
        self, api_client, user_factory, authenticate_user
    ):
        user = authenticate_user()
        receiver = user_factory()
        transaction = TransactionFactory(
            amount=100, sender=user["user_instance"], receiver=receiver
        )
        token = user["token"]
        api_client_with_credentials(token, api_client)
        url = reverse("transaction:transaction-detail", kwargs={"pk": transaction.id})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.json()["sender"] == str(user["user_instance"].id)
        assert response.json()["receiver"] == str(receiver.id)
        assert response.json()["amount"] == "100.00"

    def test_deny_retrieval_for_unowned_transaction(
        self, api_client, user_factory, authenticate_user
    ):
        """User can only retrieve transaction detail where he is a sender/recipient"""
        user = authenticate_user()
        transaction = TransactionFactory(
            amount=100, sender=user_factory(), receiver=user_factory()
        )  # Not associated with authenticated user
        token = user["token"]
        api_client_with_credentials(token, api_client)
        url = reverse("transaction:transaction-detail", kwargs={"pk": transaction.id})
        response = api_client.get(url)
        assert response.status_code == 404

    def test_transaction_amount_above_tier_limit(
        self, api_client, user_factory, authenticate_user, mocker
    ):
        mock_send_policy_violation_mail = mocker.patch(SEND_POLICY_MAIL)

        recipient = user_factory()
        recipient.created_at = datetime.now(timezone.utc) - timedelta(days=1)
        recipient.save()

        user = authenticate_user(tier="T1")
        token = user["token"]
        user_instance = user["user_instance"]

        api_client_with_credentials(token, api_client)
        data = {"recipient": f"{recipient.id}", "amount": 2_000_000}
        response = api_client.post(self.transaction_list_url, data)
        assert response.status_code == 200

        created_transaction = Transaction.objects.get(sender=user_instance)
        assert created_transaction.receiver == recipient
        assert str(created_transaction.amount) == "2000000.00"
        assert created_transaction.is_flagged == True  # Above tier limit

        email_data = {
            "email": user.get("user_instance").email,
            "message": f"Transaction amount of #2,000,000.00 is above #{TIER_AMOUNT.get(user_instance.tier):,}, your tier limit.<br>",
            "user_name": user.get("user_instance").firstname,
        }
        mock_send_policy_violation_mail.assert_called_once_with(email_data)

    def test_transaction_for_flagged_recipient(
        self, api_client, user_factory, authenticate_user, mocker
    ):
        mock_send_policy_violation_mail = mocker.patch(SEND_POLICY_MAIL)

        recipient = user_factory(is_flagged=True)
        recipient.created_at = datetime.now(timezone.utc) - timedelta(days=1)
        recipient.save()

        user = authenticate_user(tier="T1")
        token = user["token"]
        api_client_with_credentials(token, api_client)
        data = {"recipient": f"{recipient.id}", "amount": 200}
        response = api_client.post(self.transaction_list_url, data)
        assert response.status_code == 200

        email_data = {
            "email": user.get("user_instance").email,
            "message": "Recipient account is flagged.<br>",
            "user_name": user.get("user_instance").firstname,
        }
        mock_send_policy_violation_mail.assert_called_once_with(email_data)

    def test_transaction_violating_timing_window(
        self, api_client, user_factory, authenticate_user, mocker
    ):
        mock_send_policy_violation_mail = mocker.patch(SEND_POLICY_MAIL)

        recipient = user_factory()
        recipient.created_at = datetime.now(timezone.utc) - timedelta(days=1)
        recipient.save()

        user = authenticate_user(tier="T1")
        token = user["token"]

        TransactionFactory(
            sender=user.get("user_instance"), receiver=recipient
        )  # Recent transaction

        api_client_with_credentials(token, api_client)
        data = {"recipient": f"{recipient.id}", "amount": 200}
        response = api_client.post(self.transaction_list_url, data)
        assert response.status_code == 200

        email_data = {
            "email": user.get("user_instance").email,
            "message": "Transaction violated 1 minute timing window.<br>",
            "user_name": user.get("user_instance").firstname,
        }
        mock_send_policy_violation_mail.assert_called_once_with(email_data)

    def test_transaction_amount_above_max_limit(
        self, api_client, user_factory, authenticate_user, mocker
    ):
        """Max allowable limit is 5m"""
        mock_send_policy_violation_mail = mocker.patch(SEND_POLICY_MAIL)

        recipient = user_factory()
        recipient.created_at = datetime.now(timezone.utc) - timedelta(days=1)
        recipient.save()

        user = authenticate_user(tier="T3")
        token = user["token"]
        user_instance = user["user_instance"]

        api_client_with_credentials(token, api_client)
        data = {"recipient": f"{recipient.id}", "amount": 6_000_000}
        response = api_client.post(self.transaction_list_url, data)
        assert response.status_code == 200

        email_data = {
            "email": user.get("user_instance").email,
            "message": f"Transaction amount of #6,000,000.00 is above #{TIER_AMOUNT.get(user_instance.tier):,}, your tier limit.<br>Transaction amount of #6,000,000.00 is above #{MAX_TRANSACTION_AMOUNT:,} max limit<br>",
            "user_name": user.get("user_instance").firstname,
        }
        mock_send_policy_violation_mail.assert_called_once_with(email_data)
