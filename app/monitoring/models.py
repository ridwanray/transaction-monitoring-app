from datetime import datetime, timezone

from common.models import AuditableModel
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from .enums import TIER_AMOUNT
from .managers import CustomUserManager


class User(AbstractBaseUser, AuditableModel):
    TIER_CHOICES = [
        ("T1", "Tier 1"),
        ("T2", "Tier 2"),
        ("T3", "Tier 3"),
    ]
    email = models.EmailField(_("email address"), null=True, blank=True, unique=True)
    password = models.CharField(max_length=255)
    firstname = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default="T1")
    last_login = models.DateTimeField(null=True, blank=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.email

    def save_last_login(self) -> None:
        self.last_login = datetime.now(timezone.utc)
        self.save()

    @property
    def is_new(self) -> bool:
        """A user is new when created within 20mins ago"""
        allowable_in_seconds = float(20 * 60)
        now = datetime.now(timezone.utc)
        created_at = (now - self.created_at).total_seconds()
        if created_at >= allowable_in_seconds:
            return False
        return True

    def is_amount_above_tier_limit(self, amount: float) -> bool:
        """Checks if a transaction amount is within user's tier amount"""
        tier_max_amount = TIER_AMOUNT.get(self.tier)
        if amount > tier_max_amount:
            return True
        return False

    @property
    def is_within_timing_window(self):
        """Checks if the transaction is within a 1-minute timing window.
        This is based on the timing of the last transaction (sent funds) by the user.
        """
        allowable_window_in_seconds = float(1 * 60)
        if last_transaction := self.sent_funds.order_by("created_at").last():
            now = datetime.now(timezone.utc)
            time_diff = (now - last_transaction.created_at).total_seconds()
            if time_diff < allowable_window_in_seconds:
                return True
            return False

        return False


class Transaction(AuditableModel):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sent_funds"
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="received_funds",
    )
    amount = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    is_flagged = models.BooleanField(default=False)

    class Meta:
        ordering = ("-created_at",)
