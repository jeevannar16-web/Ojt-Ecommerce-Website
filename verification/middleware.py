from django.conf import settings
from django.shortcuts import redirect


class EmailVerificationMiddleware:
    ALLOWED_PREFIXES = [
        '/accounts/',
        '/verify/',
        '/users/login/',
        '/users/register/',
        '/users/logout/',
        '/users/password-reset/',
        '/admin/',
        '/static/',
        '/media/',
        '/__reload__/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, 'EMAIL_VERIFICATION_REQUIRED', True):
            return self.get_response(request)

        path = request.path_info

        if any(path.startswith(p) for p in self.ALLOWED_PREFIXES):
            return self.get_response(request)

        if request.user.is_authenticated:
            profile = getattr(request.user, 'profile', None)
            if profile and not profile.is_email_verified:
                return redirect('verification_setup')

        return self.get_response(request)
