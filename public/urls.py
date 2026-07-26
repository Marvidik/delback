from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ShipmentTrackingView,
    ShipmentAdminViewSet,LoginView
)

router = DefaultRouter()
router.register("admin/shipments", ShipmentAdminViewSet, basename="admin-shipments")

urlpatterns = [
    # Public tracking endpoint
    path(
        "track/<str:tracking_id>/",
        ShipmentTrackingView.as_view(),
        name="track-shipment",
    ),
    path("login/", LoginView.as_view(), name="login"),

    # Protected CRUD endpoints
    path("administrator/", include(router.urls)),
]