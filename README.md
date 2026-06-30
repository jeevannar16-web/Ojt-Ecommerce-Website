# FITNESS HUB — Ecommerce Platform

Full-stack Django ecommerce platform with seller marketplace, admin dashboard, real-time messaging, maps, multi-language support, and theme system. Built for production on Render.

**Live:** https://ojt-ecommerce-website.onrender.com

---

## Features

### Storefront
- Product catalog — 17 categories, 400+ products, size management
- Product detail pages with reviews, seller info, chat button
- Cart with size selection, checkout with map-based delivery picker
- Order tracking with visual timeline and delivery map
- Favorites/wishlist (CSRF-safe AJAX), flash sales, curated sections

### Authentication & Users
- Register/login with Google OAuth or email/password
- Profile with 4 tabs: Account, Orders, Wishlist, Seller
- Email verification with OTP, password reset with email confirmation
- Email validation (Check-Mail.org + MyEmailVerifier + DNS MX fallback)
- Single active session per user

### Seller Marketplace (Daraz-style)
- Apply to sell, admin approval/rejection with reason
- Seller dashboard: revenue, top products, recent orders
- Product CRUD with image upload and size management
- Order management for own products, storefront page per seller

### Admin Dashboard
- Stats: users, products, orders, revenue, pending sellers, low stock
- Order/seller management, activity log viewer with filters
- Favorites/cart overview, message center

### Messaging System
- Customer ↔ Seller conversations per product
- Seller ↔ Admin support conversations
- Real-time unread badge (polls every 5s), conversation search
- Emoji reactions, pin messages, auto-scroll

### Maps & Location
- Checkout map picker: draggable marker, reverse geocoding, "Use My Location"
- Profile map picker, order history maps, footer map
- Powered by Leaflet + OpenStreetMap (free, no API key)

### Theme System
- 4 themes: Dark, Light, Neon, Cyberpunk
- Session-persisted, dedicated picker in header

### Multi-Language & Currency
- English, Nepali, Hindi, Korean (custom `|t` filter)
- Auto-currency conversion: USD / NPR / INR / KRW
- Live exchange rates from open.er-api.com with 1-hour cache

---

## Quick Start

```bash
git clone <repo-url>
cd Ojt-Ecommerce-Website
cp .env.example .env
./start.sh
```

One command creates venv, installs deps, runs migrations, and starts the server.

Windows: `start.bat`

---

## Project Structure

| Directory | Purpose |
|-----------|---------|
| `store/` | Core app: models, views, URLs, templates, admin |
| `users/` | User profiles, auth forms, allauth adapters |
| `homepages/` | Landing page, static pages |
| `localization/` | Translation system, currency, language middleware |
| `verification/` | Email validation, OTP sending |
| `fitness_hub/` | Django project settings, URLs, wsgi |
| `templates/` | All HTML templates by app and feature |
| `static/` | CSS, JS, images (`base/` and `pages/`) |
| `fixtures/` | Seed data (446 products, 17 categories) |

---

## Tech Stack

- **Backend:** Django 5.0, Python 3.12
- **Database:** SQLite (dev) / PostgreSQL (production)
- **Static files:** Whitenoise
- **Images:** Cloudinary CDN
- **Auth:** django-allauth (email + Google OAuth)
- **Maps:** Leaflet + OpenStreetMap (no API key)
- **Deployment:** Render (free tier), GitHub Actions (keep-alive)
- **Error tracking:** Sentry

---

## Key Decisions

- Database (`db.sqlite3`) is gitignored — seed data lives in `fixtures/seed_data.json`
- Email validation runs all services in parallel; any "invalid" rejects immediately
- Verification email is NEVER auto-sent (prevents bounces)
- Admin dashboard protected by `@staff_member_required`
- Messaging uses polling (not WebSockets) — simpler deployment
- Themes use CSS custom properties with session storage
- Maps use Leaflet — no API key, completely free
- All API keys sourced from `.env` only; no hardcoded secrets
