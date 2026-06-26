"""DB-backed Translation model for multi-language content."""

from django.db import models
from django.core.cache import cache
from django.conf import settings


LANGUAGE_CHOICES = [
    ('en', 'English'),
    ('ne', 'Nepali'),
    ('hi', 'Hindi'),
    ('ko', 'Korean'),
]


# ==============================================================================
# SECTION: Language Model
# ==============================================================================

class Language(models.Model):
    code = models.CharField(max_length=10, unique=True, choices=LANGUAGE_CHOICES)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_rtl = models.BooleanField(default=False, help_text="Right-to-left script")
    flag_icon = models.CharField(max_length=10, blank=True, help_text="Emoji or icon code")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f'{self.name} ({self.code})'


# ==============================================================================
# SECTION: Translation Model
# ==============================================================================

class Translation(models.Model):
    key = models.SlugField(
        max_length=255, db_index=True,
        help_text="Unique identifier for this translation (e.g., 'home.title', 'cart.checkout')"
    )
    language = models.ForeignKey(
        Language, on_delete=models.CASCADE, related_name='translations'
    )
    value = models.TextField(help_text="Translated text")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('key', 'language')
        verbose_name_plural = 'Translations'
        ordering = ['key']

    def __str__(self):
        return f'{self.key} [{self.language.code}]: {self.value[:50]}'

    @classmethod
    def get_translations(cls, language_code, force_refresh=False):
        cache_key = f'translations_{language_code}'
        if force_refresh:
            cache.delete(cache_key)
        data = cache.get(cache_key)
        if data is not None:
            return data
        lang = Language.objects.filter(code=language_code, is_active=True).first()
        if not lang:
            return cls.get_fallback_translations()
        translations = {}
        qs = cls.objects.filter(language=lang).only('key', 'value')
        for t in qs.iterator(chunk_size=500):
            translations[t.key] = t.value
        cache.set(cache_key, translations, timeout=3600)
        return translations

    @classmethod
    def get_fallback_translations(cls):
        cache_key = 'translations_en'
        data = cache.get(cache_key)
        if data is not None:
            return data
        lang = Language.objects.filter(code='en', is_active=True).first()
        if not lang:
            return {}
        translations = {}
        for t in cls.objects.filter(language=lang).iterator(chunk_size=500):
            translations[t.key] = t.value
        cache.set(cache_key, translations, timeout=3600)
        return translations
