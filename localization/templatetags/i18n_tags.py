from django import template
from django.conf import settings

from localization.services import Translator

register = template.Library()


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
    return t.get(text, default=text)


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
