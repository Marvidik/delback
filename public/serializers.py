from rest_framework import serializers

from .models import (
    Shipment,
    ShipmentInfo,
    MovementLocation,
    DeliveryContacts,
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
    class Meta:
        model = ShipmentInfo
        exclude = ("shipment",)


class MovementLocationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = MovementLocation
        exclude = ("shipment",)


class DeliveryContactsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = DeliveryContacts
        exclude = ("shipment",)


class ShipmentSerializer(serializers.ModelSerializer):
    goods_image = serializers.URLField(
        required=False,
        allow_blank=True,
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