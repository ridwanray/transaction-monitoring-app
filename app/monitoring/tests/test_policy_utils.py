from datetime import datetime, timedelta, timezone

import pytest
import time_machine
from monitoring.models import User

from .factories import TransactionFactory

pytestmark = pytest.mark.django_db


class TestPolicyValidators:
    @pytest.mark.parametrize(
        "min_created, is_new_status",
        [
            (10, True),
            (15, True),
            (22, False),
            (25, False),
            (30, False),
        ],
    )
    def test_flag_transaction_new_user(self, user_factory, min_created, is_new_status):
        """A user is new when created within 20 min ago"""
        with time_machine.travel(
            datetime.now(timezone.utc) - timedelta(minutes=min_created)
        ):
            user = user_factory()
        user.refresh_from_db()
        assert user.is_new == is_new_status

    @pytest.mark.parametrize(
        "tier, transaction_amount, expected_transaction_flagged_status",
        [
            ("T1", 500_000, False),
            ("T1", 1_200_000, True),
            ("T2", 1_500_000, False),
            ("T2", 2_500_000, True),
            ("T3", 2_500_000, False),
            ("T3", 3_500_000, True),
        ],
    )
    def test_flag_transaction_above_tier_limit(
        self,
        tier,
        transaction_amount,
        expected_transaction_flagged_status,
        user_factory,
    ):
        user_instance: User = user_factory(tier=tier)
        transaction_status = user_instance.is_amount_above_tier_limit(
            transaction_amount
        )
        assert transaction_status == expected_transaction_flagged_status

    @pytest.mark.parametrize(
        "last_transaction_time_in_min, expected_flagged_status",
        [(1 / 2, True), (2, False), (3, False), (4, False)],
    )
    def test_flag_transaction_within_1min_window(
        self, last_transaction_time_in_min, expected_flagged_status, user_factory
    ):
        with time_machine.travel(
            datetime.now(timezone.utc) - timedelta(minutes=last_transaction_time_in_min)
        ):
            sender = user_factory()
            TransactionFactory(sender=sender, receiver=user_factory())

        sender.refresh_from_db()
        assert sender.is_within_timing_window == expected_flagged_status
