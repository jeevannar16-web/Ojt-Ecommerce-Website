from django.conf import settings
from django.core.cache import cache

from .models import Language, Translation

_cache = {}


class Translator:
    def __init__(self, language_code=None):
        self.language_code = language_code or settings.LANGUAGE_CODE
        self._translations = None
        self._fallback = None

    def _load(self):
        if self._translations is None:
            self._translations = Translation.get_translations(self.language_code)
        if self._fallback is None:
            self._fallback = Translation.get_fallback_translations()
        return self._translations, self._fallback

    def get(self, key, default=None, params=None):
        translations, fallback = self._load()
        raw = translations.get(key) or fallback.get(key) or default or key
        if params and isinstance(params, dict):
            try:
                raw = raw.format(**params)
            except (KeyError, ValueError):
                pass
        return raw

    def __call__(self, key, default=None, params=None):
        return self.get(key, default, params)

    @classmethod
    def reload_all(cls):
        for lang in Language.objects.filter(is_active=True):
            cache.delete(f'translations_{lang.code}')
        cache.delete('translations_en')
        _cache.clear()
