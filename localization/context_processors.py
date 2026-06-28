"""Localization context processors."""

from django.conf import settings

from .currency import LANG_CURRENCY, convert_price
from .models import Language, Translation
from .services import Translator



def localization_context(request):
    lang_code = getattr(request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE)
    translator = Translator(lang_code)
    available_languages = Language.objects.filter(is_active=True)

    currency_code, currency_symbol = LANG_CURRENCY.get(lang_code, ('USD', '$'))

    t = translator

    return {
        'LANGUAGE_CODE': lang_code,
        'available_languages': available_languages,
        't': t,
        'currency_code': currency_code,
        'currency_symbol': currency_symbol,
    }
