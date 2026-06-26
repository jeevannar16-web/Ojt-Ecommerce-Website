"""Management command to auto-discover and translate all |t strings in templates and views."""

import os, re, ast, time
from django.core.management.base import BaseCommand
from django.conf import settings
from localization.models import Language, Translation

try:
    from deep_translator import GoogleTranslator, MyMemoryTranslator
except ImportError:
    GoogleTranslator = None
    MyMemoryTranslator = None

MYMEMORY_EMAIL = os.getenv('MYMEMORY_EMAIL', '')

# MyMemory uses locale codes like ne-NP, hi-IN, ko-KR
MYMEMORY_LOCALE = {'ne': 'ne-NP', 'hi': 'hi-IN', 'ko': 'ko-KR'}

TARGET_LANGS = {'ne': 'Nepali', 'hi': 'Hindi', 'ko': 'Korean'}

MSG_FUNCS = {'messages.success', 'messages.error', 'messages.warning', 'messages.info'}

def _walk_and_read(base_dir, extensions):
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            if any(f.endswith(e) for e in extensions):
                with open(os.path.join(root, f), encoding='utf-8') as fh:
                    yield fh.read()

def extract_template_keys():
    keys = set()
    tdir = settings.BASE_DIR / 'templates'
    for c in _walk_and_read(tdir, ('.html', '.txt')):
        for m in re.finditer(r"\{\%\s+(?:trans|translate)\s+['\"]([^'\"]+)['\"]", c):
            keys.add(m.group(1))
        for m in re.finditer(r"['\"]([^'\"]{2,})['\"]\s*\|t", c):
            keys.add(m.group(1))
    return keys

def extract_python_keys():
    keys = set()
    seen = set()
    app_dirs = [settings.BASE_DIR / 'store', settings.BASE_DIR / 'users',
                settings.BASE_DIR / 'verification', settings.BASE_DIR / 'homepages']
    for ad in app_dirs:
        if not ad.is_dir():
            continue
        for c in _walk_and_read(ad, ('.py',)):
            # Extract f-string base text (before .format() or %)
            for m in re.finditer(r'messages\.\w+\(request,\s*(f?)["\']([^"\']{10,})["\']', c):
                base = m.group(2)
                # Remove f-string interpolation {xxx}
                base = re.sub(r'\{[^}]+\}', '{X}', base)
                if base not in seen:
                    seen.add(base)
                    keys.add(base)
            for m in re.finditer(r"JsonResponse\(\{.*?['\"](?:message|error)['\"]\s*:\s*['\"]([^'\"]{10,})['\"]", c):
                if m.group(1) not in seen:
                    seen.add(m.group(1))
                    keys.add(m.group(1))
            # Standalone user-facing strings in views: validation messages
            for m in re.finditer(r"['\"]([A-Z][^'\"]{10,}\.)['\"]", c):
                txt = m.group(1)
                if txt not in seen and any(w in txt for w in ('required', 'invalid', 'error', 'please', 'cannot', 'enter', 'select', 'provide')):
                    seen.add(txt)
                    keys.add(txt)
    return keys

def extract_db_keys():
    """Extract keys from model data (categories, choices) that use |t in templates."""
    keys = set()
    try:
        from store.models import Category
        for cat in Category.objects.all():
            if cat.name:
                keys.add(cat.name)
    except Exception:
        pass
    try:
        from users.models import Profile
        for _, label in Profile.STORE_TYPE_CHOICES:
            keys.add(label)
    except Exception:
        pass
    try:
        from store.models import Order
        for _, label in Order.STATUS_CHOICES:
            keys.add(label)
    except Exception:
        pass
    try:
        from store.models import ActivityLog
        choices = ActivityLog._meta.get_field('action_type').choices
        for _, label in choices:
            keys.add(label)
    except Exception:
        pass
    try:
        from store.models import Product
        for p in Product.objects.all():
            if p.name:
                keys.add(p.name)
    except Exception:
        pass
    return keys


def get_all_keys():
    keys = set()
    keys.update(extract_template_keys())
    keys.update(extract_python_keys())
    keys.update(extract_db_keys())
    return sorted(keys)


class Command(BaseCommand):
    help = 'Seed Translation model with auto-translated strings for ne, hi, ko'

    def get_translator(self, target_code):
        """Try MyMemory first (free API, fast), fall back to Google scraping."""
        if MyMemoryTranslator:
            try:
                locale = MYMEMORY_LOCALE.get(target_code, target_code)
                kwargs = {'source': 'en-GB', 'target': locale}
                if MYMEMORY_EMAIL:
                    kwargs['email'] = MYMEMORY_EMAIL
                t = MyMemoryTranslator(**kwargs)
                # Quick test
                test = t.translate('test')
                if test:
                    self.stdout.write(f"  ↳ MyMemory ({target_code})")
                    return t
            except Exception:
                pass
        if GoogleTranslator:
            self.stdout.write(f"  ↳ Google (scraping) ({target_code})")
            return GoogleTranslator(source='en', target=target_code)
        return None

    def handle(self, *args, **options):
        if not GoogleTranslator and not MyMemoryTranslator:
            self.stderr.write("Install: pip install deep-translator")
            return

        for code, name in TARGET_LANGS.items():
            Language.objects.get_or_create(code=code, defaults={'name': name, 'is_active': True})
        en_lang, _ = Language.objects.get_or_create(code='en', defaults={'name': 'English', 'is_active': True})

        keys = get_all_keys()
        self.stdout.write(f"Keys to translate: {len(keys)}")

        for code, lang_name in TARGET_LANGS.items():
            lang = Language.objects.get(code=code)
            existing = set(Translation.objects.filter(language=lang).values_list('key', flat=True))
            todo = [k for k in keys if k not in existing]
            self.stdout.write(f"\n--- {lang_name} ({code}): {len(todo)} new strings ---")

            if not todo:
                cnt = Translation.objects.filter(language=lang).count()
                self.stdout.write(f"  Total: {cnt}")
                continue

            trans = self.get_translator(code)
            if not trans:
                self.stderr.write(f"  ✗ No translator available for {code}")
                continue

            batch = []
            for i, key in enumerate(todo):
                if len(key) > 2000:
                    continue
                try:
                    val = trans.translate(key)
                    if val and val != key:
                        batch.append(Translation(key=key, language=lang, value=val))
                except Exception:
                    pass
                if len(batch) >= 20:
                    Translation.objects.bulk_create(batch, ignore_conflicts=True)
                    batch = []
                if (i + 1) % 30 == 0:
                    self.stdout.write(f"  {i+1}/{len(todo)}")
            if batch:
                Translation.objects.bulk_create(batch, ignore_conflicts=True)

            cnt = Translation.objects.filter(language=lang).count()
            self.stdout.write(f"  Total: {cnt}")

        # English fallback
        en_created = 0
        for key in keys:
            _, created = Translation.objects.get_or_create(key=key, language=en_lang, defaults={'value': key})
            if created:
                en_created += 1
        self.stdout.write(f"\nEnglish fallback entries created: {en_created}")
        self.stdout.write(self.style.SUCCESS("✓ Done!"))
