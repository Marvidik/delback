from django.test import TestCase

from .serializers import ShipmentSerializer


class ShipmentSerializerTests(TestCase):
    def test_serializer_accepts_multiple_goods_images(self):
        payload = {
            "origin": "Lagos",
            "destination": "Abuja",
            "carrier": "FedEx",
            "package_type": "box",
            "shipment_type": "express",
            "shipment_mode": "air",
            "product": "Phones",
            "goods_image": [
                "https://example.com/a.jpg",
                "https://example.com/b.jpg",
            ],
            "quantity": 2,
            "payment_mode": "cash",
            "total_freight": "100.00",
            "total_weight": "5.50",
            "info": {
                "reference": "REF-001",
                "latest_message": "Picked up",
                "status": "in_transit",
                "current_location": "Lagos",
                "current_location_latitude": "6.5244",
                "current_location_longitude": "3.3792",
                "movement_status": "moving",
                "expected_delivery_date": "2026-08-01",
            },
            "movement_locations": [
                {
                    "location": "Lagos",
                    "timestamp": "2026-07-30T10:00:00Z",
                    "status": "picked_up",
                    "latitude": "6.5244",
                    "longitude": "3.3792",
                }
            ],
            "delivery_contacts": [
                {
                    "contact_name": "Ada",
                    "contact_email": "ada@example.com",
                    "contact_phone": "08012345678",
                    "contact_address": "123 Main",
                    "sender_name": "John",
                    "sender_email": "john@example.com",
                    "sender_phone": "08087654321",
                    "sender_address": "456 Side",
                }
            ],
        }

        serializer = ShipmentSerializer(data=payload)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        shipment = serializer.save()

        self.assertEqual(shipment.goods_image, payload["goods_image"])
