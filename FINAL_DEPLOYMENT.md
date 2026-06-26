# E-Commerce Platform — Final Deployment Guide

## Overview

Full-stack e-commerce platform (Daraz-style) with:
- Multi-vendor marketplace (admin-approved sellers)
- Customer shopping (cart, checkout, favorites, orders)
- Real-time messaging (customer↔seller, seller↔admin)
- Admin dashboard (orders, sellers, activity log, stats)
- 4-language i18n (Nepali, Hindi, Korean, English) with live currency conversion
- Email verification + deliverability validation
- Map-based delivery location picker
- Chat themes (19 themes, dark/light/wallpaper)

**Stack:** Django 5.0.6, Python 3.12, SQLite, Leaflet/OpenStreetMap

---

## How to Recreate This Project

### 1. Prerequisites
```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment
Copy `.env.example` to `.env` and fill in:
- `SECRET_KEY` — generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `CHECKMAIL_API_KEY` — from check-mail.org (1,000 free/month)
- `MYEMAILVERIFIER_API_KEY` — from client.myemailverifier.com (100 free/day)
- `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` — Gmail App Password

### 3. Database
```bash
python manage.py migrate
python manage.py seed_realistic    # 6 sellers, 50 users, 446 products, 148 orders
python manage.py seed_translations  # 680 translations per language
```

### 4. Static Files
```bash
python manage.py collectstatic --noinput
```

### 5. Run
```bash
python manage.py runserver 0.0.0.0:8000
```

### 6. Superuser
```bash
python manage.py createsuperuser
# Username: jeevan, Email: jeevannar16@gmail.com
```

---

## Project Architecture

### Directory Layout
```
Ojt-Ecommerce-Website/
├── homepages/          # Landing page app
│   └── templates/homepages/index.html
├── store/              # Core e-commerce app
│   ├── views/          # Module package (9 modules)
│   │   ├── __init__.py
│   │   ├── product_views.py
│   │   ├── cart_views.py
│   │   ├── checkout_views.py
│   │   ├── order_views.py
│   │   ├── review_views.py
│   │   ├── messaging_views.py
│   │   └── seller_views.py
│   ├── admin_dashboard_views.py
│   ├── seller_views.py
│   ├── models.py
│   └── urls.py
├── users/              # User accounts + profiles
│   ├── models.py       # Profile, CredentialHistory
│   └── verification/   # Email validation + OTP
├── localization/       # i18n + currency
│   ├── currency.py     # Live FX rates (open.er-api.com)
│   └── templatetags/   # |t filter, |currency filter
├── templates/
│   ├── layout/         # base.html, messages_base.html
│   ├── store/          # product_list, product_detail, cart, checkout, etc.
│   │   ├── seller/     # Seller dashboard, products, apply
│   │   ├── messages/   # Chat detail, list, customer detail
│   │   └── account/    # Profile, orders, wishlist
│   └── includes/       # Reusable components
├── static/
│   ├── css/
│   │   ├── base/       # reset, variables, navigation, footer, scrollbar, etc.
│   │   ├── pages/      # Page-specific CSS (messages, admin, seller, etc.)
│   │   └── responsive.css  # Daraz-style mobile/tablet layout
│   ├── js/
│   │   ├── base/       # theme, loading, main, cart, favorites, etc.
│   │   └── pages/      # Page-specific JS
│   └── img/themes/     # 19 chat theme preview images
└── verification/       # Email validation app
```

### Key Models
- `Product` — title, price, description, category, images, seller (FK User), size options
- `ProductSize` — size per product with stock tracking
- `CartItem` — user, product, quantity, size
- `Order` / `OrderItem` — full order lifecycle with status tracking
- `Conversation` / `Message` — real-time messaging with reactions, pin, edit, delete
- `Profile` — address, phone, seller status, lat/lng for delivery
- `CredentialHistory` — saved seller application data per user
- `ActivityLog` — admin audit trail
- `Translation` — DB-backed i18n keys
- `EmailValidation` — OTP-based verification codes

---

## Backup Procedure

### Database (SQLite — single file)
```bash
# Manual
cp db.sqlite3 db.sqlite3.$(date +%Y%m%d_%H%M%S).bak

# Automated (cron: daily at 3 AM)
0 3 * * * cd /path/to/project && cp db.sqlite3 backups/db.sqlite3.$(date +\%Y\%m\%d).bak

# Restore
cp backups/db.sqlite3.20260626.bak db.sqlite3
```

### Media Files (photos, uploads)
```bash
# Full media backup
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/

# Rsync to remote
rsync -avz media/ user@backup-server:/backups/project-media/

# S3 sync (optional)
aws s3 sync media/ s3://my-bucket/production/media/
```

### Bulk Export Commands
```bash
# All users
python manage.py dumpdata auth.User --indent 2 > backup_users.json

# All products
python manage.py dumpdata store.Product store.ProductSize --indent 2 > backup_products.json

# All orders
python manage.py dumpdata store.Order store.OrderItem --indent 2 > backup_orders.json

# Full database (excluding transient session data)
python manage.py dumpdata --exclude sessions --exclude contenttypes --exclude admin.logentry --indent 2 > full_backup.json

# Restore from dump
python manage.py loaddata full_backup.json
```

### Static Files
```bash
python manage.py collectstatic --noinput
# Then backup the STATIC_ROOT directory
```

### Environment Variables
```bash
cp .env .env.$(date +%Y%m%d).bak
```

### Complete Snapshot
```bash
#!/bin/bash
# backup.sh — run from project root
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/$DATE"
mkdir -p "$BACKUP_DIR"
cp db.sqlite3 "$BACKUP_DIR/"
cp .env "$BACKUP_DIR/"
tar -czf "$BACKUP_DIR/media.tar.gz" media/
python manage.py dumpdata --exclude sessions --exclude contenttypes --exclude admin.logentry --indent 2 > "$BACKUP_DIR/data.json"
echo "Backup complete: $BACKUP_DIR"
```

---

## API Keys & Secrets

| Variable | Service | Status |
|----------|---------|--------|
| `SECRET_KEY` | Django | CHANGE IN PRODUCTION |
| `CHECKMAIL_API_KEY` | check-mail.org | Active (1,000/mo free) |
| `MYEMAILVERIFIER_API_KEY` | client.myemailverifier.com | Active (100/day free) |
| `ZEROBOUNCE_API_KEY` | zerobounce.net | Empty (not configured) |
| `NEVERBOUNCE_API_KEY` | neverbounce.com | Empty (trial expired) |
| `EMAIL_HOST_PASSWORD` | Gmail SMTP | Active App Password |
| `GOOGLE_CLIENT_SECRET` | Google OAuth | Active |

All keys stored in `.env` (gitignored). No keys hardcoded in source files.

---

## Deployment Checklist

- [ ] `SECRET_KEY` changed from default
- [ ] `DEBUG = False` in settings.py
- [ ] `ALLOWED_HOSTS` = production domain(s)
- [ ] Database migrated (`python manage.py migrate`)
- [ ] Static files collected (`python manage.py collectstatic`)
- [ ] `.env` file present on server
- [ ] Apache/Nginx serving static/media files
- [ ] HTTPS configured (Cloudflare Tunnel or certbot)
- [ ] Email backend configured for production
- [ ] Regular backup cron job set up
- [ ] Monitoring (error logging, uptime check)

---

## Key Views & URLs

| URL Pattern | View | Purpose |
|-------------|------|---------|
| `/` | `homepages.views.index` | Landing page with categories, featured products |
| `/products/` | `store.views.product_list` | Category-filtered product grid |
| `/product/<id>/` | `store.views.product_detail` | Product detail + reviews + seller card |
| `/cart/` | `store.views.cart_detail` | Shopping cart with size/qty management |
| `/checkout/` | `store.views.checkout` | Map picker + order review |
| `/orders/` | `store.views.order_history` | Customer order history |
| `/profile/` | `store.views.profile_view` | Account/Orders/Wishlist/Seller tabs |
| `/admin/dashboard/` | `store.admin_dashboard_views` | Admin stats + seller approval + order mgmt |
| `/seller/` | `store.seller_views.dashboard` | Seller stats + product CRUD + orders |
| `/seller/apply/` | `store.seller_views.apply` | Seller application with credential history |
| `/messages/` | `store.views.messaging_views` | Chat list + conversation detail |
