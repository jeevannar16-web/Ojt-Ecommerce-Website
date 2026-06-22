from django.conf import settings

from .models import Language, Translation
from .services import Translator


def localization_context(request):
    lang_code = getattr(request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE)
    translator = Translator(lang_code)
    available_languages = Language.objects.filter(is_active=True)

    t = translator

    return {
        'LANGUAGE_CODE': lang_code,
        'available_languages': available_languages,
        't': t,
        'trans': t,
    }
