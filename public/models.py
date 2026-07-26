from django.db import models,transaction

# Create your models here.
class Shipment(models.Model):

    origin = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    carrier = models.CharField(max_length=255)
    tracking_id = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
    )

    package_type = models.CharField(max_length=20)

    shipment_type = models.CharField(max_length=20)

    shipment_mode = models.CharField(max_length=20)

    product = models.CharField(max_length=255)

    quantity = models.PositiveIntegerField(default=1)

    payment_mode = models.CharField(max_length=20)

    total_freight = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Shipping cost"
    )

    total_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Weight in kilograms"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            creating = self.pk is None

            super().save(*args, **kwargs)

            if creating and not self.tracking_id:
                self.tracking_id = f"EXSD-{self.id:06d}"
                super().save(update_fields=["tracking_id"])

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.origin} → {self.destination}"




class ShipmentInfo(models.Model):
    shipment = models.OneToOneField(Shipment, on_delete=models.CASCADE, related_name='info')
    reference = models.CharField(max_length=100)
    latest_message = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    current_location = models.CharField(max_length=255)
    movement_status = models.CharField(max_length=50)
    expected_delivery_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Shipment {self.reference}"



class MovementLocation(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='movement_locations')
    location = models.CharField(max_length=255)
    timestamp = models.DateTimeField()
    status = models.CharField(max_length=50)

    def __str__(self):
        return f"Movement at {self.location} for Shipment {self.shipment.shipment_id}"


class DeliveryContacts(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='delivery_contacts')
    contact_name = models.CharField(max_length=100)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    contact_address = models.TextField()
    sender_name = models.CharField(max_length=100)
    sender_email = models.EmailField()
    sender_phone = models.CharField(max_length=20)
    sender_address = models.TextField()

    def __str__(self):
        return f"Contact {self.contact_name} for Shipment {self.shipment.shipment_id}"
