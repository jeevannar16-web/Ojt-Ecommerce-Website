"""Language middleware."""

import threading

from django.conf import settings

from .models import Language

_thread_locals = threading.local()


def get_current_language():
    return getattr(_thread_locals, 'language_code', settings.LANGUAGE_CODE)


class LanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang_code = self._resolve_language(request)
        request.LANGUAGE_CODE = lang_code
        _thread_locals.language_code = lang_code
        if hasattr(request, 'session'):
            request.session['django_language'] = lang_code
        response = self.get_response(request)
        _thread_locals.language_code = None
        if not response.cookies.get('django_language'):
            response.set_cookie('django_language', lang_code, max_age=31536000)
        return response

    def _resolve_language(self, request):
        path_parts = request.path_info.split('/')
        if len(path_parts) > 1 and path_parts[1]:
            codes = dict(Language.objects.filter(is_active=True).values_list('code', 'code'))
            if path_parts[1] in codes:
                return path_parts[1]
        lang = request.GET.get('lang')
        if lang and Language.objects.filter(code=lang, is_active=True).exists():
            return lang
        if hasattr(request, 'session') and request.session.get('django_language'):
            return request.session['django_language']
        lang = request.COOKIES.get('django_language')
        if lang and Language.objects.filter(code=lang, is_active=True).exists():
            return lang
        return settings.LANGUAGE_CODE
