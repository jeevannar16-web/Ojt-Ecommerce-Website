"""Centralized activity logging — records admin and user actions for the audit trail in the dashboard."""

from .models import ActivityLog


def log_action(user, action_type, description='', details=None, request=None):
    ip = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
    ActivityLog.objects.create(
        user=user,
        action_type=action_type,
        description=description,
        details=details or {},
        ip_address=ip,
    )
