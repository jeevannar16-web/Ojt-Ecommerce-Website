from django.contrib.sessions.models import Session
from django.utils import timezone
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver


@receiver(user_logged_in)
def remove_other_sessions(sender, user, request, **kwargs):
    """Delete all other sessions for this user when they log in."""
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    for session in sessions:
        data = session.get_decoded()
        if data.get('_auth_user_id') == str(user.pk) and \
           session.session_key != request.session.session_key:
            session.delete()
