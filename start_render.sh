#!/bin/bash
# start_render.sh — Render start command
set -e

python manage.py migrate --noinput

# Auto-setup script — superuser, Google OAuth, site domain
python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness_hub.settings')
django.setup()
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

# Create superuser
if not User.objects.filter(username='jeevan').exists():
    User.objects.create_superuser('jeevan', 'admin@fitnesshub.com', 'REPLACED_ADMIN_PASS')
    print('Superuser created: jeevan / REPLACED_ADMIN_PASS')
else:
    print('Superuser already exists')

# Update site domain from BASE_URL
domain = os.environ.get('BASE_URL', 'https://ojt-ecommerce-website.onrender.com').replace('https://','').replace('http://','').split('/')[0]
Site.objects.update_or_create(id=1, defaults={'domain': domain, 'name': domain})
print(f'Site domain set to: {domain}')

# Auto-configure Google login from env vars
client_id = os.environ.get('GOOGLE_CLIENT_ID')
client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
if client_id and client_secret:
    app, created = SocialApp.objects.get_or_create(
        provider='google',
        defaults={'name': 'Google', 'client_id': client_id, 'secret': client_secret}
    )
    if not created:
        app.client_id = client_id
        app.secret = client_secret
        app.save()
    site = Site.objects.get(id=1)
    app.sites.add(site)
    print('Google OAuth configured')
else:
    print('Google OAuth skipped — set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET env vars')
" 2>&1

exec gunicorn fitness_hub.wsgi:application --workers=4 --threads=2 --worker-class=gthread
