# ==============================================================================
# Module: verification.admin
# Description: Admin configuration for verification app
# ==============================================================================

from django.contrib import admin

from .models import EmailVerification, PhoneVerification


# ==============================================================================
# SECTION: EmailVerification Admin
# ==============================================================================

@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'email', 'is_verified', 'verified_at', 'created_at', 'expires_at', 'is_expired']
    list_filter = ['is_verified', 'is_expired', 'created_at']
    search_fields = ['user__username', 'user__email', 'email']
    readonly_fields = ['token', 'otp']


# ==============================================================================
# SECTION: PhoneVerification Admin
# ==============================================================================

@admin.register(PhoneVerification)
class PhoneVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'is_verified', 'verified_at', 'created_at', 'expires_at', 'is_expired']
    list_filter = ['is_verified', 'is_expired', 'created_at']
    search_fields = ['user__username', 'phone']
    readonly_fields = ['otp']
