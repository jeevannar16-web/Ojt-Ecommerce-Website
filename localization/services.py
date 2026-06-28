"""Translation service — fetches and stores translations from external APIs."""

from django.conf import settings
from django.core.cache import cache

from .models import Language, Translation

_cache = {}


# ==============================================================================
# SECTION: Translator Class
# ==============================================================================

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
        raw = translations.get(key) or fallback.get(key)
        if raw is None:
            raw = self._fallback_text(key) if default is None else default
        if params and isinstance(params, dict):
            try:
                raw = raw.format(**params)
            except (KeyError, ValueError):
                pass
        return raw

    @staticmethod
    def _fallback_text(key):
        fallbacks = {
            'nav.login': 'Login',
            'nav.register': 'Register',
            'nav.logout': 'Logout',
            'nav.profile': 'Profile',
            'nav.cart': 'Cart',
            'nav.admin_dashboard': 'Admin Dashboard',
            'nav.seller_dashboard': 'Seller Dashboard',
            'home.hero_title': 'Premium Fitness Gear',
            'home.hero_subtitle': 'Curated fitness goods, beautifully delivered. Find what moves you.',
            'home.shop_now': 'Shop Now →',
            'home.featured': 'Featured Products',
            'home.new_arrivals': 'New Arrivals',
            'profile.orders': 'My Orders',
        }
        return fallbacks.get(key) or key.split('.')[-1].replace('_', ' ').title()

    def __call__(self, key, default=None, params=None):
        return self.get(key, default, params)

    @classmethod
    def reload_all(cls):
        for lang in Language.objects.filter(is_active=True):
            cache.delete(f'translations_{lang.code}')
        cache.delete('translations_en')
        _cache.clear()
