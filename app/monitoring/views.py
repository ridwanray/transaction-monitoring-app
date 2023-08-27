from django.contrib.auth import get_user_model
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Transaction, User
from .serializers import (
    CustomObtainTokenPairSerializer,
    MakeTransactionSerializer,
    OnboardUserSerializer,
    PasswordChangeSerializer,
    TransactionSerializer,
    UpdateUserSerializer,
    UserSerializer,
)


class CustomObtainTokenPairView(TokenObtainPairView):
    """Authentice with email and password"""

    serializer_class = CustomObtainTokenPairSerializer


class PasswordChangeView(viewsets.GenericViewSet):
    """Enables authenticated users to change their passwords."""

    serializer_class = PasswordChangeSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        context = {"request": request}
        serializer = self.get_serializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Your password has been updated."}, status.HTTP_200_OK
        )


class UserViewsets(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = [
        "get",
        "post",
        "patch",
    ]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = [
        "email",
        "firstname",
    ]
    ordering_fields = [
        "created_at",
        "email",
        "firstname",
    ]

    def get_queryset(self):
        user: User = self.request.user
        if user.is_admin:
            return super().get_queryset().all()
        return super().get_queryset().filter(id=user.id)

    def get_serializer_class(self):
        if self.action == "create":
            return OnboardUserSerializer
        if self.action in ["partial_update"]:
            return UpdateUserSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        permission_classes = self.permission_classes
        if self.action in ["create"]:
            permission_classes = [AllowAny]
        elif self.action in ["list", "retrieve", "partial_update", "update"]:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @extend_schema(responses={200: UserSerializer()})
    def create(self, request, *args, **kwargs):
        """Accounts are automatically activated upon creation."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "message": "Account Created!"}, status=200)

    def list(self, request, *args, **kwargs):
        """Retrieve a list of users.\n
        Only admins can retrieve the complete list of users in the system.
        """
        return super().list(request, *args, **kwargs)

    @extend_schema(responses={200: UserSerializer()})
    def partial_update(self, request, *args, **kwargs):
        """Enables a user to update the tier, flag status, and admin status for a specified user."""
        return super().partial_update(request, *args, **kwargs)


class TransactionViewSets(viewsets.ModelViewSet):
    queryset = Transaction.objects.all().select_related("sender", "receiver")
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post"]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["is_flagged"]
    search_fields = ["sender__firstname", "receiver__firstname", "amount"]
    ordering_fields = [
        "created_at",
    ]

    def get_serializer_class(self):
        if self.action in ["create"]:
            return MakeTransactionSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        user: User = self.request.user
        return Transaction.objects.filter(Q(sender=user) | Q(receiver=user)).distinct()

    def list(self, request, *args, **kwargs):
        """Retrieve transactions associated with an authenticated user."""
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Initiate a transfer from an authenticated user to another user.\n
        Transactions are restricted to occur between the same accounts.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "success": True,
                "message": "Transaction made successfully!",
            },
            status.HTTP_200_OK,
        )
