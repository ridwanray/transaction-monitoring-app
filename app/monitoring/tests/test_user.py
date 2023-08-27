import pytest
from django.urls import reverse
from monitoring.models import User

from .conftest import api_client_with_credentials

pytestmark = pytest.mark.django_db


class TestUser:
    user_list_url = reverse("user:user-list")

    def test_create_user(self, api_client):
        data = {
            "email": "ray@ridwanray.com",
            "password": "secretpass@",
            "firstname": "Ray",
        }
        response = api_client.post(self.user_list_url, data)
        assert response.status_code == 200

        user_instance = User.objects.get(email=data["email"])
        assert user_instance.check_password(data["password"])
        assert user_instance.firstname == data["firstname"]

    def test_deny_create_user_duplicate_email(self, api_client, active_user):
        """Prevent user creation due to duplicate email."""
        data = {
            "email": active_user.email,
            "password": "simplepass@",
            "firstname": "Ray",
        }
        response = api_client.post(self.user_list_url, data)
        assert response.status_code == 400

    def test_admin_retrieve_all_users(
        self, api_client, user_factory, authenticate_user
    ):
        user_factory.create_batch(3)
        user = authenticate_user(is_admin=True)
        token = user["token"]
        api_client_with_credentials(token, api_client)
        response = api_client.get(self.user_list_url)
        assert response.status_code == 200
        assert response.json()["total"] == 4  # 3 users + admin

    def test_nonadmin_retrieve_personal_data(
        self, api_client, user_factory, authenticate_user
    ):
        """Non admin users retrieve only their data"""
        user_factory.create_batch(3)
        user = authenticate_user(is_admin=False)
        token = user["token"]
        api_client_with_credentials(token, api_client)
        response = api_client.get(self.user_list_url)
        assert response.status_code == 200
        assert response.json()["total"] == 1

    def test_retrieve_user_by_id(self, api_client, authenticate_user):
        user = authenticate_user(is_admin=False)
        user_instance: User = user["user_instance"]
        token = user["token"]
        api_client_with_credentials(token, api_client)
        url = reverse("user:user-detail", kwargs={"pk": user_instance.id})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.json()["firstname"] == user_instance.firstname
        assert response.json()["tier"] == user_instance.tier

    def test_update_user(self, api_client, authenticate_user):
        user = authenticate_user(tier="T1", is_admin=False)
        user_instance: User = user["user_instance"]
        token = user["token"]
        api_client_with_credentials(token, api_client)
        url = reverse("user:user-detail", kwargs={"pk": user_instance.id})
        data = {"is_flagged": False, "tier": "T2", "is_admin": True}
        response = api_client.patch(url, data)
        assert response.status_code == 200
        user_instance.refresh_from_db()
        assert response.json()["tier"] == data["tier"]
        assert response.json()["is_flagged"] == data["is_flagged"]
        assert user_instance.tier == data["tier"]
        assert user_instance.is_admin == data["is_admin"]
