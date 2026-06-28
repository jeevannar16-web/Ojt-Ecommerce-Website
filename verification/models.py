"""Verification models."""

import secrets
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings


OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 15


def _generate_otp():
    return ''.join(str(secrets.randbelow(10)) for _ in range(OTP_LENGTH))


def _generate_token():
    return secrets.token_urlsafe(32)



class EmailVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verifications')
    email = models.EmailField()
    token = models.CharField(max_length=64, unique=True, default=_generate_token)
    otp = models.CharField(max_length=10, default=_generate_otp)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    is_expired = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_verified']),
            models.Index(fields=['token']),
            models.Index(fields=['otp']),
        ]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
        if not self.token:
            self.token = _generate_token()
        if not self.otp:
            self.otp = _generate_otp()
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        return (not self.is_verified
                and not self.is_expired
                and timezone.now() <= self.expires_at)

    def verify_otp(self, submitted_otp):
        if not self.is_valid:
            return False
        if self.otp == submitted_otp.strip():
            self.is_verified = True
            self.verified_at = timezone.now()
            self.user.is_active = True
            self.user.save(update_fields=['is_active'])
            self.save(update_fields=['is_verified', 'verified_at'])
            return True
        return False

    def verify_token(self, submitted_token):
        if not self.is_valid:
            return False
        if self.token == submitted_token.strip():
            self.is_verified = True
            self.verified_at = timezone.now()
            self.save(update_fields=['is_verified', 'verified_at'])
            return True
        return False

    def expire(self):
        self.is_expired = True
        self.save(update_fields=['is_expired'])

    @classmethod
    def cleanup_expired(cls):
        expired = cls.objects.filter(
            is_verified=False,
            is_expired=False,
            expires_at__lte=timezone.now()
        )
        count = expired.update(is_expired=True)
        return count

    def __str__(self):
        return f'{self.user.username} → {self.email} [{"✓" if self.is_verified else "✗"}]'



class PhoneVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phone_verifications')
    phone = models.CharField(max_length=20)
    otp = models.CharField(max_length=10, default=_generate_otp)
    provider_sid = models.CharField(max_length=255, blank=True, help_text="Provider-specific ID (e.g., Twilio SID)")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    is_expired = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_verified']),
            models.Index(fields=['phone']),
        ]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        return (not self.is_verified
                and not self.is_expired
                and timezone.now() <= self.expires_at)

    def verify_otp(self, submitted_otp):
        if not self.is_valid:
            return False
        if self.otp == submitted_otp.strip():
            self.is_verified = True
            self.verified_at = timezone.now()
            self.save(update_fields=['is_verified', 'verified_at'])
            return True
        return False

    def expire(self):
        self.is_expired = True
        self.save(update_fields=['is_expired'])

    @classmethod
    def cleanup_expired(cls):
        expired = cls.objects.filter(
            is_verified=False,
            is_expired=False,
            expires_at__lte=timezone.now()
        )
        count = expired.update(is_expired=True)
        return count

    def __str__(self):
        return f'{self.user.username} → {self.phone} [{"✓" if self.is_verified else "✗"}]'
