"""Phone verification service."""

import logging
import re

from django.conf import settings
from django.utils import timezone

from .models import PhoneVerification
from .sms_providers import get_sms_provider

logger = logging.getLogger(__name__)



class PhoneVerificationService:
    provider = None

    @classmethod
    def _get_provider(cls):
        if cls.provider is None:
            cls.provider = get_sms_provider()
        return cls.provider

    @staticmethod
    def format_phone(phone: str, country_code: str = None) -> str:
        cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)
        if not cleaned.startswith('+'):
            country = country_code or getattr(settings, 'DEFAULT_COUNTRY_CODE', 'US')
            from phonenumbers import parse, format_number, PhoneNumberFormat
            try:
                parsed = parse(cleaned, country)
                cleaned = format_number(parsed, PhoneNumberFormat.E164)
            except Exception:
                cleaned = '+' + cleaned if not cleaned.startswith('+') else cleaned
        return cleaned

    @classmethod
    def send_otp(cls, user, phone: str) -> tuple:
        """
        Send an OTP to the given phone number.
        Returns (success: bool, message: str, verification: PhoneVerification|None)
        """
        formatted = cls.format_phone(phone)
        PhoneVerification.objects.filter(
            user=user, phone=formatted, is_verified=False
        ).update(is_expired=True)

        verification = PhoneVerification.objects.create(
            user=user,
            phone=formatted,
        )

        provider = cls._get_provider()
        result = provider.send_otp(formatted, verification.otp)

        if result.get('sid'):
            verification.provider_sid = result['sid']
            verification.save(update_fields=['provider_sid'])
            logger.info(f'OTP sent via {provider.get_provider_name()} to {formatted}')
            return True, 'Verification code sent', verification
        else:
            verification.expire()
            error = result.get('error', 'Failed to send SMS')
            logger.error(f'SMS send failed for {formatted}: {error}')
            return False, error, None

    @classmethod
    def verify_otp(cls, user, otp: str) -> tuple:
        verification = PhoneVerification.objects.filter(
            user=user, is_verified=False, is_expired=False
        ).first()
        if not verification:
            return False, 'No pending verification found'

        if verification.expires_at < timezone.now():
            verification.expire()
            return False, 'OTP has expired. Request a new one.'

        provider = cls._get_provider()
        provider_ok = provider.verify_otp(verification.phone, otp)

        if provider_ok and verification.verify_otp(otp):
            profile = getattr(user, 'profile', None)
            if profile:
                profile.phone = verification.phone
                profile.is_phone_verified = True
                profile.save(update_fields=['phone', 'is_phone_verified'])
            return True, 'Phone verified successfully'
        if not provider_ok:
            return False, 'Verification failed at provider level'
        return False, 'Invalid OTP'

    @classmethod
    def resend(cls, user, phone: str) -> tuple:
        cooldown_minutes = getattr(settings, 'VERIFICATION_COOLDOWN_MINUTES', 1)
        formatted = cls.format_phone(phone)
        recent = PhoneVerification.objects.filter(
            user=user, phone=formatted, is_verified=False, is_expired=False
        ).first()
        if recent:
            elapsed = (timezone.now() - recent.created_at).total_seconds()
            if elapsed < cooldown_minutes * 60:
                remaining = int(cooldown_minutes * 60 - elapsed)
                return False, f'Please wait {remaining} seconds before resending', None
            recent.expire()
        success, msg, verification = cls.send_otp(user, formatted)
        return success, msg, verification
