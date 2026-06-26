"""Management command to clean up expired verification records."""

from django.core.management.base import BaseCommand
from verification.models import EmailVerification, PhoneVerification


class Command(BaseCommand):
    help = 'Clean up expired email and phone verifications'

    def handle(self, *args, **options):
        email_count = EmailVerification.cleanup_expired()
        phone_count = PhoneVerification.cleanup_expired()
        self.stdout.write(
            self.style.SUCCESS(
                f'Expired: {email_count} email, {phone_count} phone verifications'
            )
        )
