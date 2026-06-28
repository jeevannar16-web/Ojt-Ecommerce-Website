"""Template tags for translation (|t) and currency (|currency) filters."""

from django import template
from django.conf import settings

from localization.currency import convert_price
from localization.services import Translator
from localization.middleware import get_current_language

register = template.Library()


# ==============================================================================
# SECTION: Translation Tags
# ==============================================================================

@register.simple_tag(takes_context=True)
def trans(context, key, default=None, **params):
    lang_code = context.get('LANGUAGE_CODE') or settings.LANGUAGE_CODE
    t = Translator(lang_code)
    return t.get(key, default, params=params or None)


@register.simple_tag(takes_context=True)
def translate(context, key, default=None, **params):
    return trans(context, key, default, **params)


@register.filter
def translate_str(text, lang_code='en'):
    t = Translator(lang_code)
    text = str(text) if not isinstance(text, str) else text
    return t.get(text)

@register.filter
def ttrans(key, lang_code):
    t = Translator(lang_code)
    key = str(key) if not isinstance(key, str) else key
    return t.get(key)

_cur_lang = None

@register.filter
def t(key):
    lang_code = get_current_language()
    tr = Translator(lang_code)
    key = str(key) if not isinstance(key, str) else key
    return tr.get(key)


@register.simple_tag(takes_context=True)
def lang_url(context, target_lang):
    request = context.get('request')
    if not request:
        return '/'
    from localization.middleware import LanguageMiddleware
    return LanguageMiddleware.process_url(request.get_full_path(), target_lang)


@register.simple_tag(takes_context=True)
def switch_lang(context, target_lang):
    return lang_url(context, target_lang)


# ==============================================================================
# SECTION: Currency Filter
# ==============================================================================

@register.filter
def currency(value, arg=None):
    lang_code = arg or get_current_language()
    converted, code, symbol = convert_price(value or 0, lang_code)
    return f'{symbol}{converted:,.2f}'
