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
python -c "
import django, os, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness_hub.settings')
django.setup()
from django.conf import settings
from store.models import Product, Category

fixture_path = os.path.join(settings.BASE_DIR, 'fixtures/seed_data.json')
with open(fixture_path) as f:
    data = json.load(f)

product_images = {e['pk']: e['fields'].get('image') for e in data if e['model'] == 'store.product'}
cat_images = {e['pk']: e['fields'].get('image') for e in data if e['model'] == 'store.category'}

fixed = 0
for p in Product.objects.all():
    if not p.image and p.pk in product_images and product_images[p.pk]:
        p.image = product_images[p.pk]
        p.save(update_fields=['image'])
        fixed += 1
for c in Category.objects.all():
    if not c.image and c.pk in cat_images and cat_images[c.pk]:
        c.image = cat_images[c.pk]
        c.save(update_fields=['image'])
        fixed += 1
if fixed:
    print(f'Restored images for {fixed} products/categories from fixture')
" 2>&1

# Auto-setup script (ensures superuser, Site, and SocialApp exist)
python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness_hub.settings')
django.setup()
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

# --- Ensure superuser jeevan exists with correct password ---
user, created = User.objects.get_or_create(
    username='jeevan',
    defaults={'email': 'admin@fitnesshub.com', 'is_superuser': True, 'is_staff': True}
)
user.set_password('REPLACED_ADMIN_PASS')
user.is_superuser = True
user.is_staff = True
user.save()
print(f'Superuser {\"created\" if created else \"updated\"}: jeevan / REPLACED_ADMIN_PASS')

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

exec gunicorn fitness_hub.wsgi:application --workers=4 --threads=2 --worker-class=gthread
