from django.contrib import admin

from .models import (
    Shipment,
    ShipmentInfo,
    MovementLocation,
    DeliveryContacts,
)


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("tracking_id", "origin", "destination", "product", "goods_image")
    search_fields = ("tracking_id", "origin", "destination", "product")
    readonly_fields = ("tracking_id", "created_at", "updated_at")


@admin.register(ShipmentInfo)
class ShipmentInfoAdmin(admin.ModelAdmin):
    list_display = (
        "shipment",
        "reference",
        "status",
        "current_location",
        "current_location_latitude",
        "current_location_longitude",
        "expected_delivery_date",
    )
    search_fields = ("reference", "status", "current_location")


@admin.register(MovementLocation)
class MovementLocationAdmin(admin.ModelAdmin):
    list_display = ("shipment", "location", "timestamp", "status", "latitude", "longitude")
    list_filter = ("status",)


@admin.register(DeliveryContacts)
class DeliveryContactsAdmin(admin.ModelAdmin):
    list_display = ("shipment", "contact_name", "sender_name")
    search_fields = ("contact_name", "sender_name", "contact_email", "sender_email")
