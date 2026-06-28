"""Email sending service."""

import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from .models import EmailVerification

logger = logging.getLogger(__name__)



class EmailVerificationService:
    @staticmethod
    def create_and_send(user, email=None):
        target_email = email or user.email
        if not target_email:
            raise ValueError(f'User {user.username} has no email address')

        EmailVerification.objects.filter(
            user=user, email=target_email, is_verified=False
        ).update(is_expired=True)

        verification = EmailVerification.objects.create(
            user=user,
            email=target_email,
        )

        EmailVerificationService._send_otp_email(verification)
        logger.info(f'Verification email sent to {target_email}')

        return verification

    @staticmethod
    def _send_otp_email(verification):
        subject = 'Verify your email address'
        context = {
            'user': verification.user,
            'otp': verification.otp,
            'token': verification.token,
            'expires_in': '15 minutes',
            'base_url': settings.BASE_URL,
        }
        html_message = render_to_string('verification/email_otp.html', context)
        text_message = (
            f'Your verification code is: {verification.otp}\n'
            f'Or click: {settings.BASE_URL or "http://localhost:8000"}'
            f'/verify/email/{verification.token}/\n'
            f'Expires in 15 minutes.'
        )
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@fitnesshub.com',
            recipient_list=[verification.email],
            html_message=html_message,
            fail_silently=False,
        )

    @staticmethod
    def verify_otp(user, otp):
        verification = EmailVerification.objects.filter(
            user=user, is_verified=False, is_expired=False
        ).first()
        if not verification:
            return False, 'No pending verification found'
        if verification.expires_at < timezone.now():
            verification.expire()
            return False, 'OTP has expired. Request a new one.'
        if verification.verify_otp(otp):
            profile = getattr(user, 'profile', None)
            if profile:
                profile.is_email_verified = True
                profile.save(update_fields=['is_email_verified'])
            return True, 'Email verified successfully'
        return False, 'Invalid OTP'

    @staticmethod
    def verify_token(token):
        try:
            verification = EmailVerification.objects.get(token=token, is_verified=False)
        except EmailVerification.DoesNotExist:
            return False, 'Invalid or already used verification link'
        if verification.expires_at < timezone.now():
            verification.expire()
            return False, 'Verification link has expired'
        verification.verify_token(token)
        profile = getattr(verification.user, 'profile', None)
        if profile:
            profile.is_email_verified = True
            profile.save(update_fields=['is_email_verified'])
        return True, 'Email verified successfully'

    @staticmethod
    def resend(user, email=None):
        target_email = email or user.email
        cooldown_minutes = getattr(settings, 'VERIFICATION_COOLDOWN_MINUTES', 1)
        recent = EmailVerification.objects.filter(
            user=user, email=target_email, is_verified=False, is_expired=False
        ).first()
        if recent:
            elapsed = (timezone.now() - recent.created_at).total_seconds()
            if elapsed < cooldown_minutes * 60:
                remaining = int(cooldown_minutes * 60 - elapsed)
                return False, f'Please wait {remaining} seconds before resending'
            recent.expire()

        try:
            verification = EmailVerificationService.create_and_send(user, target_email)
            return True, verification
        except Exception as e:
            return False, f'Failed to send: {e}'
