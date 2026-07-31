from django.shortcuts import render

# Create your views here.
from rest_framework.generics import RetrieveAPIView
from .models  import Shipment, Wallets
from .serializers import ShipmentSerializer, WalletSerializer
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.viewsets import ModelViewSet
# views.py

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from rest_framework.authentication import TokenAuthentication

from .serializers import LoginSerializer


class LoginView(APIView):
    permission_classes = [AllowAny]


    @extend_schema(
        request=LoginSerializer,
        responses={200: dict},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "token": token.key,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                },
            },
            status=status.HTTP_200_OK,
        )

class ShipmentTrackingView(RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = ShipmentSerializer
    lookup_field = "tracking_id"

    queryset = Shipment.objects.select_related(
        "info"
    ).prefetch_related(
        "movement_locations",
        "delivery_contacts"
    )



class ShipmentAdminViewSet(ModelViewSet):
    serializer_class = ShipmentSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = Shipment.objects.select_related(
        "info"
    ).prefetch_related(
        "movement_locations",
        "delivery_contacts"
    )




class WalletViewSet(ModelViewSet):
    serializer_class = WalletSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = Wallets.objects.all()


from rest_framework import generics
from rest_framework.permissions import AllowAny

class WalletListView(generics.ListAPIView):
    queryset = Wallets.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [AllowAny]




from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .brevo import BrevoEmailError, send_otp_email
from .models import PasswordResetOTP
from .serializers import VerifyOtpChangePasswordSerializer


def _get_admin_user():
    """
    Fetches the single hardcoded admin account by email.
    Set ADMIN_EMAIL in settings.py — this is the only account this flow will ever touch.
    """
    User = get_user_model()
    return User.objects.get(email=settings.ADMIN_EMAIL)


class OTPRequestThrottle(AnonRateThrottle):
    scope = "otp_request"


class OTPVerifyThrottle(AnonRateThrottle):
    scope = "otp_verify"


class RequestPasswordChangeOTPView(APIView):
    """
    POST, no payload, no auth required.
    Generates an OTP for the hardcoded admin account and emails it via Brevo.
    """
    permission_classes = [AllowAny]
    throttle_classes = [OTPRequestThrottle]

    def post(self, request):
        try:
            user = _get_admin_user()
        except get_user_model().DoesNotExist:
            # Misconfiguration on your side, not the caller's — don't leak details
            return Response(
                {"detail": "Unable to process request."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        _, raw_code = PasswordResetOTP.generate_for_user(user)

        try:
            send_otp_email(
                to_email=user.email,
                to_name=getattr(user, "get_full_name", lambda: "")() or user.username,
                otp_code=raw_code,
            )
        except BrevoEmailError:
            # Don't leak provider details to the client
            return Response(
                {"detail": "Failed to send verification email. Please try again."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {"detail": "A verification code has been sent to your email."},
            status=status.HTTP_200_OK,
        )


class VerifyOtpChangePasswordView(APIView):
    """
    POST { "otp": "123456", "new_password": "..." }
    No auth required. Validates the OTP against the hardcoded admin account
    and, if valid, updates that account's password.
    """
    permission_classes = [AllowAny]
    throttle_classes = [OTPVerifyThrottle]

    def post(self, request):
        serializer = VerifyOtpChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp_code = serializer.validated_data["otp"]
        new_password = serializer.validated_data["new_password"]

        try:
            user = _get_admin_user()
        except get_user_model().DoesNotExist:
            return Response(
                {"detail": "Unable to process request."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        otp_instance = (
            PasswordResetOTP.objects.filter(user=user, is_used=False)
            .order_by("-created_at")
            .first()
        )

        if not otp_instance or not otp_instance.is_valid():
            return Response(
                {"detail": "No valid verification code found. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not otp_instance.check_code(otp_code):
            remaining = max(0, 5 - otp_instance.attempts)
            return Response(
                {"detail": f"Incorrect code. {remaining} attempt(s) remaining."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Success — consume the OTP and set the new password
        otp_instance.mark_used()
        user.set_password(new_password)
        user.save(update_fields=["password"])

        return Response(
            {"detail": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )