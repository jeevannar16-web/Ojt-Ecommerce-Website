#!/bin/bash
# start_render.sh — Render start command
set -e

echo "=== START_RENDER.SH STARTED ==="
date
pwd
ls -la fixtures/ 2>&1 || echo "No fixtures dir"

python manage.py migrate --noinput

# --- Load full seed data (products, users, translations, etc.) if DB is empty ---
python -c "
import django, os, sys, traceback
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness_hub.settings')
django.setup()
from store.models import Product
count = Product.objects.count()
print(f'Products in DB before load: {count}')
if count < 10:
    from django.core.management import call_command
    from django.db import IntegrityError, connection
    # Clear conflicting data before loading fixture
    from store.models import NewsletterSubscriber
    NewsletterSubscriber.objects.all().delete()
    print('Cleared NewsletterSubscriber table')
    try:
        from django.conf import settings
        fixture_path = os.path.join(settings.BASE_DIR, 'fixtures/seed_data.json')
        call_command('loaddata', fixture_path, verbosity=0)
    except IntegrityError as e:
        print(f'IntegrityError: {e}')
        # Try without transaction wrapping
        connection.set_autocommit(True)
        try:
            call_command('loaddata', fixture_path, verbosity=0)
        except Exception as e2:
            print(f'Second attempt also failed: {e2}')
    except Exception as e:
        print(f'ERROR loading fixture: {e}')
        traceback.print_exc()
    count = Product.objects.count()
    print(f'Products in DB after load: {count}')
else:
    print('Skipping fixture load — products already exist')
" 2>&1

# --- Restore product/category images from fixture if they were cleared ---
python manage.py fix_product_images 2>&1 || echo "Image restoration skipped (non-fatal)"

# Auto-setup script (ensures superuser, Site, and SocialApp exist)
python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness_hub.settings')
django.setup()
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

# --- List all existing admin/staff accounts ---
staff = User.objects.filter(is_staff=True)
if staff.exists():
    print('Staff/superuser accounts in DB:')
    for u in staff:
        print(f'  - {u.username} (email: {u.email}, superuser: {u.is_superuser}, staff: {u.is_staff})')
else:
    print('No staff accounts found')

# --- Ensure superuser jeevan exists with correct password ---
admin_email = os.environ.get('ADMIN_EMAIL', 'jeevanadmin@outlook.com')
user, created = User.objects.get_or_create(
    username='jeevan',
    defaults={'email': admin_email, 'is_superuser': True, 'is_staff': True}
)
user.set_password('REPLACED_ADMIN_PASS')
user.is_superuser = True
user.is_staff = True
user.save()
print(f'Superuser {"created" if created else "updated"}: jeevan / REPLACED_ADMIN_PASS (email: {user.email})')

# --- Site domain ---
domain = os.environ.get('BASE_URL', 'https://ojt-ecommerce-website.onrender.com').replace('https://','').replace('http://','').split('/')[0]
Site.objects.update_or_create(id=1, defaults={'domain': domain, 'name': domain})
print(f'Site domain: {domain}')

# --- Google OAuth ---
client_id = os.environ.get('GOOGLE_CLIENT_ID')
client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
if client_id and client_secret:
    app, _ = SocialApp.objects.get_or_create(
        provider='google',
        defaults={'name': 'Google', 'client_id': client_id, 'secret': client_secret}
    )
    if not _:
        app.client_id = client_id
        app.secret = client_secret
        app.save()
    site = Site.objects.get(id=1)
    app.sites.add(site)
    print('Google OAuth configured')
else:
    SocialApp.objects.get_or_create(
        provider='google',
        defaults={'name': 'Google', 'client_id': 'placeholder', 'secret': 'placeholder'}
    )
    print('Google OAuth placeholder created (set GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET env vars)')
" 2>&1

# Reduce workers for free tier (Render caps at 1 CPU)
exec gunicorn fitness_hub.wsgi:application \
  --workers=2 --threads=2 --worker-class=gthread \
  --timeout 120 --keep-alive 60
