from rest_framework import serializers

from .models import (
    Shipment,
    ShipmentInfo,
    MovementLocation,
    DeliveryContacts,
    Wallets,
)
from django.contrib.auth import authenticate



class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username=attrs["username"],
            password=attrs["password"],
        )

        if not user:
            raise serializers.ValidationError(
                "Invalid username or password."
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "This account is inactive."
            )

        attrs["user"] = user
        return attrs


class ShipmentInfoSerializer(serializers.ModelSerializer):
    current_location_latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
    )
    current_location_longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = ShipmentInfo
        exclude = ("shipment",)


class MovementLocationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
    )
    longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = MovementLocation
        exclude = ("shipment",)


class DeliveryContactsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = DeliveryContacts
        exclude = ("shipment",)


class GoodsImageField(serializers.ListField):
    child = serializers.URLField(allow_blank=False)

    def to_internal_value(self, data):
        if data in (None, ""):
            return []

        if isinstance(data, str):
            data = [data]

        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as exc:
            raise serializers.ValidationError("Expected a URL string or a list of URL strings.") from exc

    def to_representation(self, value):
        if value in (None, ""):
            return []
        return super().to_representation(value)


class ShipmentSerializer(serializers.ModelSerializer):
    goods_image = GoodsImageField(
        required=False,
        allow_null=True,
    )
    info = ShipmentInfoSerializer(required=True)
    movement_locations = MovementLocationSerializer(
        many=True,
        required=True,
    )
    delivery_contacts = DeliveryContactsSerializer(
        many=True,
        required=True,
    )

    class Meta:
        model = Shipment
        fields = "__all__"
        read_only_fields = (
            "id",
            "tracking_id",
            "created_at",
            "updated_at",
        )

    def create(self, validated_data):
        info_data = validated_data.pop("info")
        movement_data = validated_data.pop("movement_locations")
        contact_data = validated_data.pop("delivery_contacts")

        shipment = Shipment.objects.create(**validated_data)

        ShipmentInfo.objects.create(
            shipment=shipment,
            **info_data,
        )

        for movement in movement_data:
            MovementLocation.objects.create(
                shipment=shipment,
                **movement,
            )

        for contact in contact_data:
            DeliveryContacts.objects.create(
                shipment=shipment,
                **contact,
            )

        return shipment

    def update(self, instance, validated_data):
        info_data = validated_data.pop("info", None)
        movement_data = validated_data.pop("movement_locations", None)
        contact_data = validated_data.pop("delivery_contacts", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if info_data:
            ShipmentInfo.objects.update_or_create(
                shipment=instance,
                defaults=info_data,
            )

        if movement_data is not None:
            instance.movement_locations.all().delete()

            for movement in movement_data:
                MovementLocation.objects.create(
                    shipment=instance,
                    **movement,
                )

        if contact_data is not None:
            instance.delivery_contacts.all().delete()

            for contact in contact_data:
                DeliveryContacts.objects.create(
                    shipment=instance,
                    **contact,
                )

        return instance




class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallets
        fields = "__all__"
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )



