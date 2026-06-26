# ==============================================================================
# Module: verification.apps
# Description: Verification app configuration
# ==============================================================================

from django.apps import AppConfig


class VerificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'verification'
    verbose_name = 'Email & Phone Verification'
