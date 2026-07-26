from django.shortcuts import render

# Create your views here.
from rest_framework.generics import RetrieveAPIView
from .models  import Shipment
from .serializers import ShipmentSerializer
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