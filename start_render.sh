#!/bin/bash
# start_render.sh — Render start command
set -e

python manage.py migrate --noinput

# Create superuser if it doesn't exist
python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness_hub.settings')
django.setup()
from django.contrib.auth.models import User
if not User.objects.filter(username='jeevan').exists():
    User.objects.create_superuser('jeevan', 'admin@fitnesshub.com', 'REPLACED_ADMIN_PASS')
    print('Superuser created: jeevan / REPLACED_ADMIN_PASS')
else:
    print('Superuser already exists')
" 2>&1

exec gunicorn fitness_hub.wsgi:application --workers=4 --threads=2 --worker-class=gthread
