from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Transaction, User
from .tasks import send_policy_email
from .utils import evaluate_policy


class CustomObtainTokenPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        access_token = refresh.access_token
        self.user.save_last_login()
        data["refresh"] = str(refresh)
        data["access"] = str(access_token)
        return data

    @classmethod
    def get_token(cls, user: User):
        if user.is_flagged:
            raise exceptions.AuthenticationFailed(
                _("Account flagged! Contact Admin."), code="authentication"
            )
        token = super().get_token(user)
        token.id = user.id
        token["firstname"] = user.firstname
        token["email"] = user.email
        return token


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=128)
    new_password = serializers.CharField(max_length=128, min_length=4)

    def validate_old_password(self, value):
        request = self.context["request"]

        if not request.user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def save(self):
        user: User = self.context["request"].user
        new_password = self.validated_data["new_password"]
        user.set_password(new_password)
        user.save(update_fields=["password"])


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class UpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "email",
            "firstname",
            "is_active",
            "is_flagged",
            "is_admin",
            "tier",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
            "email": {"read_only": True},
            "firstname": {"read_only": True},
            "is_active": {"read_only": True},
        }


class OnboardUserSerializer(serializers.Serializer):
    """Serializer for creating user object"""

    firstname = serializers.CharField(min_length=3)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=4)

    def validate(self, attrs: dict):
        email = attrs.get("email")
        cleaned_email = email.lower().strip()
        if get_user_model().objects.filter(email__iexact=cleaned_email).exists():
            raise serializers.ValidationError({"email": "User exists with this email"})
        return super().validate(attrs)

    def create(self, validated_data: dict):
        data = {
            "email": validated_data.get("email"),
            "password": make_password(validated_data.get("password")),
            "firstname": validated_data.get("firstname"),
            "is_active": True,
        }
        user: User = User.objects.create(**data)
        return user


class TransactionSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.firstname", read_only=True)
    recipient_name = serializers.CharField(source="receiver.firstname", read_only=True)

    class Meta:
        model = Transaction
        fields = "__all__"


class MakeTransactionSerializer(serializers.Serializer):
    recipient = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        error_messages={
            "does_not_exist": "No matching User found with id'{pk_value}'",
        },
    )
    amount = serializers.DecimalField(max_digits=20, decimal_places=2, min_value=1.0)

    def validate(self, attrs):
        """Sender and recipient are expected to differ"""
        auth_user: User = self.context["request"].user
        if auth_user == attrs["recipient"]:
            raise serializers.ValidationError(
                {"recipient": "You cannot tranfer into your account!"}
            )
        return super().validate(attrs)

    def create(self, validated_data: dict):
        auth_user: User = self.context["request"].user
        recipient = validated_data.get("recipient")
        amount = validated_data.get("amount")
        evaluation_result = evaluate_policy(
            auth_user, recipient, validated_data.get("amount")
        )
        transaction_flagged = evaluation_result.get("is_flagged")
        data = {
            "sender": auth_user,
            "receiver": recipient,
            "amount": amount,
            "is_flagged": transaction_flagged,
        }
        transaction = Transaction.objects.create(**data)
        if transaction_flagged:
            send_policy_email.delay(
                {
                    "email": auth_user.email,
                    "message": evaluation_result.get("violation_message"),
                    "user_name": auth_user.firstname,
                }
            )
        return transaction


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "email",
            "firstname",
            "is_active",
            "is_flagged",
            "is_admin",
            "tier",
        ]
