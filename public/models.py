from django.db import models,transaction
import secrets
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

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
    map_movement = models.BooleanField(default=False, help_text="Indicates if the shipment's movement should be tracked in real time in FE")

    package_type = models.CharField(max_length=20)

    shipment_type = models.CharField(max_length=20)

    shipment_mode = models.CharField(max_length=20)

    product = models.CharField(max_length=255)

    goods_image = models.JSONField(
        default=list,
        blank=True,
        null=True,
        help_text="List of image URLs for the goods",
    )

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
                random_part = secrets.randbelow(900000) + 100000
                self.tracking_id = f"EXSD-{random_part}-{self.id}"
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
    current_location_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
    )
    current_location_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
    )
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
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"Movement at {self.location} for Shipment {self.shipment.tracking_id}"


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
        return f"Contact {self.contact_name} for Shipment {self.shipment.tracking_id}"



class Wallets(models.Model):
    show_wallet = models.BooleanField(default=False)
    coin = models.CharField(max_length=50)
    wallet_address = models.CharField(max_length=255)
    network = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet for  all Shipment "


 
OTP_LENGTH = 6
OTP_TTL_MINUTES = 10
MAX_ATTEMPTS = 5
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
class PasswordResetOTP(models.Model):
    """
    One row per OTP request. The raw code is never stored — only its hash,
    same as a password. Old unused OTPs for a user are invalidated whenever
    a new one is generated.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_otps",
    )
    code_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)
 
    class Meta:
        ordering = ["-created_at"]
 
    @classmethod
    def generate_for_user(cls, user):
        """
        Invalidate any previous unused OTPs, create a new one, and return
        (instance, raw_code). raw_code is what gets emailed — it's not
        retrievable again afterwards.
        """
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
 
        raw_code = "".join(secrets.choice("0123456789") for _ in range(OTP_LENGTH))
        instance = cls.objects.create(
            user=user,
            code_hash=make_password(raw_code),
            expires_at=timezone.now() + timezone.timedelta(minutes=OTP_TTL_MINUTES),
        )
        return instance, raw_code
 
    def is_valid(self):
        return (
            not self.is_used
            and self.attempts < MAX_ATTEMPTS
            and timezone.now() <= self.expires_at
        )
 
    def check_code(self, raw_code):
        """Verifies the code and increments the attempt counter regardless of outcome."""
        self.attempts += 1
        self.save(update_fields=["attempts"])
        return check_password(raw_code, self.code_hash)
 
    def mark_used(self):
        self.is_used = True
        self.save(update_fields=["is_used"])
 