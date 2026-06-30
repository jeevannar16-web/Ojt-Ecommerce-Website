# About Fitness Hub

## Overview

Fitness Hub is a full-stack Django ecommerce platform for fitness products. It supports multi-vendor seller marketplace, real-time messaging, multi-language/currency, map-based delivery, and a rich theme system. Deployed on Render (free tier).

**Live:** https://ojt-ecommerce-website.onrender.com

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   Browser                        │
│  HTML + CSS (Whitenoise) + JS (deferred)         │
│  Images from Cloudinary CDN                      │
│  Maps from Leaflet + OpenStreetMap               │
└─────────────┬───────────────────────────────────┘
              │ HTTPS
┌─────────────▼───────────────────────────────────┐
│              Render (Gunicorn)                    │
│  Django 5.0.14 · Python 3.12                     │
│  Whitenoise (compressed, 1yr cache)              │
│  LocMemCache (server-side)                       │
│  SQLite (dev) / PostgreSQL (prod)                │
└─────────────┬───────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────┐
│          External Services                        │
│  Cloudinary — product image CDN + thumbnails     │
│  Google OAuth — social login                     │
│  Open Exchange Rates — currency conversion       │
│  Check-Mail.org / MyEmailVerifier — email check  │
│  MyMemory — translation fallback                 │
│  Sentry — error tracking                         │
└─────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Django 5.0.14 | Web framework |
| **Language** | Python 3.12 | Runtime |
| **Database** | SQLite / PostgreSQL | Data storage |
| **Auth** | django-allauth | Login, Google OAuth, email/password |
| **Static files** | Whitenoise | Serve CSS/JS with compression + manifest |
| **Images** | Cloudinary | CDN + auto-resize thumbnails (`|img_url` filter) |
| **Maps** | Leaflet + OpenStreetMap | Location picker, delivery map |
| **Deployment** | Render (free tier) | Hosting |
| **CI** | GitHub Actions | Keep-alive ping, deployment status |
| **Error tracking** | Sentry | Error monitoring |
| **Frontend** | Vanilla JS + CSS | No frameworks — pure Django templates |
| **Icons** | Bootstrap Icons | UI icons |
| **Fonts** | Google Fonts (Playfair Display) | Typography |
| **Translation** | Custom `\|t` filter + MyMemory API | Multi-language (EN, NE, HI, KO) |
| **Currency** | Open Exchange Rates API | USD/NPR/INR/KRW conversion |

---

## Directory Structure

```
fitness_hub/          # Django project settings, root URLs, WSGI config
  settings.py         # All settings, env vars, Whitenoise, cache
  urls.py             # Root URL routing
  wsgi.py             # WSGI app for Gunicorn

store/                # Core app — models, views, templates, admin
  models.py           # Product, Category, Order, Review, Cart, etc.
  admin.py            # Django admin config
  views/              # View modules
    product_views.py  # Product list, detail, catalog
    cart_views.py     # Add to cart, update, remove
    checkout_views.py # Checkout flow + distance-based delivery pricing
    order_views.py    # Order tracking, history
    favorites_views.py# Wishlist/favorites
    search_views.py   # Product search
    seller_views.py   # Seller dashboard, product management
    review_views.py   # Product reviews
  templatetags/
    store_extras.py   # Custom filters (|img_url, |t, |currency)

users/                # User profiles, auth, allauth adapter
  models.py           # Profile model (seller status, bio)
  adapter.py          # Google OAuth adapter (saves avatar, name)

homepages/            # Landing page, static pages (about, contact)
  views.py            # Home view, static pages

localization/         # Translation + currency system
  middleware.py       # Language + currency middleware
  templatetags/       # |t filter, |currency filter
  Translator()        # Handles translation caching

verification/         # Email validation + OTP
  email_service.py    # Send emails via SMTP (from noreply@fitnesshub.com)
  views.py            # OTP verify, password reset

templates/            # All HTML templates
  layout/             # Base layout, header, footer, navigation
  store/              # Product pages, cart, checkout, orders
  users/              # Profile, login, register
  homepages/          # Home, about, contact
  includes/           # Reusable partials

static/               # CSS + JS
  css/base/           # loading.css, main.css, nav.css, etc.
  css/pages/          # Page-specific CSS (product_list, product_detail, etc.)
  js/base/            # loading.js, main.js, cart.js, mini_cart.js, etc.
  js/pages/           # product_detail.js, product_list.js, etc.
```

---

## Key Features Explained

### Product Images
- Stored on **Cloudinary** CDN.
- Custom `|img_url` filter resizes images per context:
  - Cards: 300×300 (grid, recommendations)
  - Detail: 600×600 (main image)
  - Cart: 100×100 (mini cart, checkout list)
- The product detail page shows a pulsing skeleton overlay until the image finishes loading.

### Delivery Pricing
- **Haversine formula** calculates straight-line distance from store origin (27.72°N, 85.32°E — Kathmandu).
- Tiers: free ≤5km → $14.99 >300km.
- Express adds $5.99 flat.
- Stored as `delivery_charge` on the Order model.

### Authentication
- **Two backends**: Django ModelBackend + allauth AuthenticationBackend.
- Google OAuth via `django-allauth` with a custom adapter that saves avatar and full name.
- All credentials from `.env` (never hardcoded).

### Messaging
- Polling-based (every 5s), not WebSockets — simpler on Render free tier.
- Three conversation types: Customer↔Seller (per product), Seller↔Admin (support).
- Emoji reactions, pin messages, unread badges.

### Themes
- 13 themes via CSS custom properties, session-persisted.
- Picker in header and mobile hamburger menu.

### Multi-Language
- Custom `|t` template filter translates strings.
- MyMemory API as primary, with fallback.
- Supported: English, Nepali, Hindi, Korean.
- 1-hour cache per translation key.

### Currency
- Auto-detected by language: EN→USD, NE→NPR, HI→INR, KO→KRW.
- Live rates from open.er-api.com, 1-hour cache.

---

## No-Reply Email

The system sends transactional emails (OTP, password reset, order confirmations) from:
```
Fitness Hub <noreply@fitnesshub.com>
```

Configured in:
- `fitness_hub/settings.py` — `DEFAULT_FROM_EMAIL` (env var or fallback)
- `.env` — `DEFAULT_FROM_EMAIL` override

To use a real SMTP server, uncomment the email section in `.env` and set your SMTP credentials. Emails are only sent for OTP verification and password resets — **never auto-sent** unsolicited.

---

## Security

| Practice | Detail |
|----------|--------|
| `.env` | All secrets stored here, gitignored, chmod 600 |
| No hardcoded keys | Sentry DSN, OAuth IDs, Cloudinary keys all from env |
| CSRF | All mutation endpoints protected |
| HSTS | Headers enforced in production |
| Staff protection | Admin, curation, seller approval require staff/superuser |
| Sessions | Single active session per user |
| Password min length | 8 characters |
| `.gitignore` | `.env`, `db.sqlite3`, `__pycache__`, `*.pyc` |

---

## Performance Optimizations

1. **Cloudinary thumbnails** — images auto-resized per context (75-90% smaller payload)
2. **Whitenoise compression** — `CompressedManifestStaticFilesStorage` + 1-year cache
3. **Async CSS** — Google Fonts + Leaflet load with `media="print" onload="this.media='all'"` (non-blocking)
4. **Deferred JS** — all non-critical scripts use `defer`, no render blocking
5. **Database indexes** — 6 indexes on Product model (sale, featured, rating, created_at, stock, price)
6. **Low-memory queries** — home view uses `cache.set()` instead of loading all product IDs
7. **Page loader** — instant visual feedback on every navigation click
8. **Image skeleton** — pulsing placeholder on product detail while image loads

---

## Deployment

- **Host:** Render (free tier), auto-deploys from GitHub `main` branch
- **Keep alive:** GitHub Actions pings the site every 10 minutes (prevents Render free-tier spin-down)
- **Status:** GitHub Actions workflow (`deployment_status.yml`) marks each commit with ✅/❌
- **Database:** Render provisions PostgreSQL automatically (via `render.yaml` or dashboard)
- **Static files:** Whitenoise serves them directly — no CDN needed for CSS/JS

### Environment Variables (Render Dashboard)
```
SECRET_KEY=<django secret key>
DEBUG=False
BASE_URL=https://ojt-ecommerce-website.onrender.com
CLOUD_NAME=your-cloud-name
CLOUD_API_KEY=your-api-key
CLOUD_API_SECRET=your-api-secret
DEFAULT_FROM_EMAIL=Fitness Hub <noreply@fitnesshub.com>
```

---

## Local Development

```bash
git clone <repo-url>
cd Ojt-Ecommerce-Website
cp .env.example .env
./start.sh     # Linux/macOS
start.bat       # Windows
```

The `start.sh` script:
1. Creates Python venv (if missing)
2. Installs dependencies
3. Runs `migrate`
4. Starts the dev server on port 8000

The SQLite database (`db.sqlite3`) is in `.gitignore`. The repo includes `fixtures/seed_data.json` (446 products, 17 categories) — load it with:
```bash
python manage.py loaddata fixtures/seed_data.json
```
