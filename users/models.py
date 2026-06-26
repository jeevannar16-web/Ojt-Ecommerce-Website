# ==============================================================================
# Module: users.models
# Description: User profile and credential history models
# ==============================================================================

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


# ==============================================================================
# SECTION: Profile Model
# ==============================================================================

class Profile(models.Model):
    STORE_TYPE_CHOICES = [
        ('individual', 'Individual / Sole Proprietor'),
        ('company', 'Company / Business Entity'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    age = models.IntegerField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    goal = models.CharField(max_length=100, blank=True)
    medical_conditions = models.TextField(blank=True)
    is_seller = models.BooleanField(default=False, help_text="Can this user access the seller dashboard?")
    seller_requested = models.BooleanField(default=False, help_text="User has requested seller access, pending admin approval")
    seller_rejection_reason = models.TextField(blank=True, help_text="If seller request was declined, why")
    seller_requested_at = models.DateTimeField(null=True, blank=True, help_text="When the user last requested seller access")
    phone = models.CharField(max_length=20, blank=True, help_text="Contact phone number")
    address_line1 = models.CharField(max_length=255, blank=True, help_text="Street address")
    address_line2 = models.CharField(max_length=255, blank=True, help_text="Apartment, suite, etc.")
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True, default='US')
    store_name = models.CharField(max_length=200, blank=True, help_text="Your store/business name")
    store_slug = models.SlugField(max_length=200, blank=True, help_text="URL slug for your public store page")
    business_type = models.CharField(max_length=20, choices=STORE_TYPE_CHOICES, blank=True, help_text="Type of seller account")
    store_description = models.TextField(blank=True, help_text="Describe what you sell")
    business_registration = models.CharField(max_length=200, blank=True, help_text="Business registration / license number")
    tax_id = models.CharField(max_length=200, blank=True, help_text="Tax ID / VAT number")
    id_proof = models.ImageField(upload_to='seller_docs/', blank=True, null=True, help_text="Government ID or business license")
    business_address = models.TextField(blank=True, help_text="Registered business address")
    is_email_verified = models.BooleanField(default=False, help_text="Email verified via OTP")
    is_phone_verified = models.BooleanField(default=False, help_text="Phone verified via SMS OTP")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Default delivery latitude")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Default delivery longitude")
    status_emoji = models.CharField(max_length=10, blank=True, default='🟢', help_text="Custom status emoji (e.g. 🟢, 🔴, 🌙, ⛔)")
    status_text = models.CharField(max_length=100, blank=True, default='Available', help_text="Custom status text (e.g. Available, Busy, At work, Away)")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, help_text="Profile photo")

    def __str__(self):
        return self.user.username


# ==============================================================================
# SECTION: CredentialHistory Model
# ==============================================================================

class CredentialHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credential_history')
    store_name = models.CharField(max_length=200, blank=True)
    business_type = models.CharField(max_length=20, blank=True)
    store_description = models.TextField(blank=True)
    business_registration = models.CharField(max_length=200, blank=True)
    tax_id = models.CharField(max_length=200, blank=True)
    business_address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'credential histories'

    def __str__(self):
        return f"{self.user.username} — {self.store_name or 'no name'} ({self.created_at:%Y-%m-%d})"


# ==============================================================================
# SECTION: Signal Handlers
# ==============================================================================

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if kwargs.get('raw', False):
        return
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)
