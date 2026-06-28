#!/bin/bash
# start_render.sh — Render start command
set -e

python manage.py migrate --noinput

# Auto-setup script
python -c "
import django, os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness_hub.settings')
django.setup()
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from store.models import Category, Product

# --- Create superuser ---
if not User.objects.filter(username='jeevan').exists():
    User.objects.create_superuser('jeevan', 'admin@fitnesshub.com', 'REPLACED_ADMIN_PASS')
    print('Superuser created: jeevan / REPLACED_ADMIN_PASS')
else:
    print('Superuser already exists')

# --- Site domain ---
domain = os.environ.get('BASE_URL', 'https://ojt-ecommerce-website.onrender.com').replace('https://','').replace('http://','').split('/')[0]
Site.objects.update_or_create(id=1, defaults={'domain': domain, 'name': domain})
print(f'Site domain: {domain}')

# --- Google OAuth ---
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
    # Create placeholder so Google button doesn't 500
    SocialApp.objects.get_or_create(
        provider='google',
        defaults={'name': 'Google', 'client_id': 'placeholder', 'secret': 'placeholder'}
    )
    print('Google OAuth placeholder created (set GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET env vars)')

# --- Seed categories if empty ---
if not Category.objects.exists():
    cats = ['Cardio', 'Strength', 'Yoga', 'Accessories', 'Supplements', 'Clothing', 'Recovery']
    for name in cats:
        Category.objects.create(name=name)
    print(f'Categories created: {len(cats)}')
else:
    print(f'Categories already exist: {Category.objects.count()}')

# --- Seed sample products if empty ---
if not Product.objects.exists():
    seller = User.objects.filter(username='jeevan').first()
    if seller:
        from decimal import Decimal
        import random
        samples = [
            ('Treadmill Pro X1', 'High-quality treadmill', 899.99, 'Cardio'),
            ('Dumbbell Set 20kg', 'Adjustable dumbbell pair', 149.99, 'Strength'),
            ('Yoga Mat Premium', 'Non-slip thick mat', 39.99, 'Yoga'),
            ('Resistance Bands Set', '5-level bands', 24.99, 'Accessories'),
            ('Whey Protein 2kg', 'Chocolate flavor', 59.99, 'Supplements'),
            ('Gym T-Shirt', 'Breathable cotton', 19.99, 'Clothing'),
            ('Foam Roller', 'Muscle recovery roller', 29.99, 'Recovery'),
        ]
        for name, desc, price, cat_name in samples:
            cat = Category.objects.filter(name=cat_name).first()
            Product.objects.create(
                name=name, description=desc, price=Decimal(str(price)),
                category=cat, seller=seller, stock=random.randint(5, 50)
            )
        print(f'Sample products created: {len(samples)}')
else:
    print(f'Products already exist: {Product.objects.count()}')
" 2>&1

exec gunicorn fitness_hub.wsgi:application --workers=4 --threads=2 --worker-class=gthread
