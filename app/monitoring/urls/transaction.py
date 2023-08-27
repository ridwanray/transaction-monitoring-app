from django.urls import include, path
from rest_framework.routers import DefaultRouter

from ..views import TransactionViewSets

app_name = "transaction"

router = DefaultRouter()
router.register("", TransactionViewSets)

urlpatterns = [
    path("", include(router.urls)),
]
