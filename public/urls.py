from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    RequestPasswordChangeOTPView,
    ShipmentTrackingView,
    ShipmentAdminViewSet,LoginView,
    VerifyOtpChangePasswordView,
    WalletListView,WalletViewSet
)

router = DefaultRouter()
router.register("admin/shipments", ShipmentAdminViewSet, basename="admin-shipments")
router.register("admin/wallets",WalletViewSet,basename="admin-wallets")

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
    path("wallets/", WalletListView.as_view(), name="wallet-list"),

     path(
        "password-change/request-otp/",
        RequestPasswordChangeOTPView.as_view(),
        name="password-change-request-otp",
    ),
    path(
        "password-change/verify/",
        VerifyOtpChangePasswordView.as_view(),
        name="password-change-verify",
    ),
]