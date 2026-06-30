# FITNESS HUB — Ecommerce Platform

Full-stack Django ecommerce platform with seller marketplace, admin dashboard, real-time messaging, maps, multi-language support, and theme system. Built for production on Render.

**Live:** https://ojt-ecommerce-website.onrender.com

[![Render Deployment](https://img.shields.io/badge/deployment-pending-ff69b4)](https://github.com/jeevannar16-web/Ojt-Ecommerce-Website/actions)

---

## Features

### Storefront
- Product catalog — 17 categories, 400+ products, size management
- Product detail pages with image zoom, rating breakdown, reviews, seller info
- Cart with size selection, checkout with map-based delivery picker
- **Distance-based delivery pricing** — standard delivery cost varies by distance (Haversine formula)
- Order tracking with visual timeline and delivery map
- Favorites/wishlist (CSRF-safe AJAX), flash sales, curated sections
- **Responsive design** — mobile-first with hamburger menu

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
- 13 themes: Obsidian, Dark, Gold, Neon, Cyberpunk, and more
- Session-persisted, dedicated picker in header and mobile menu

### Multi-Language & Currency
- English, Nepali, Hindi, Korean (custom `|t` filter)
- Auto-currency conversion: USD / NPR / INR / KRW
- Live exchange rates from open.er-api.com with 1-hour cache

---

## Performance Optimizations

| Feature | Detail |
|---------|--------|
| **Cloudinary thumbnails** | Images auto-resized: 300×300 on cards, 600×600 on detail, 100×100 on cart |
| **CSS/JS compression** | Whitenoise CompressedManifestStaticFilesStorage with 1-year cache |
| **Non-blocking CSS** | Google Fonts and Leaflet load asynchronously (`media="print"` trick) |
| **Deferred JS** | All non-critical scripts use `defer` — no render blocking |
| **Database indexes** | 6 indexes on Product model for common filter fields |
| **Page loader** | Instant loading spinner on every navigation click |
| **Low-memory queries** | Home view no longer loads all product IDs into memory |

---

## Quick Start

```bash
git clone <repo-url>
cd Ojt-Ecommerce-Website
cp .env.example .env
./start.sh
```

One command creates venv, installs deps, and starts the server. The database (`db.sqlite3`) is included in the repo — products and data come pre-loaded.

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
| `.github/workflows/` | GitHub Actions: keep-alive + deployment status |

---

## Tech Stack

- **Backend:** Django 5.0, Python 3.12
- **Database:** SQLite (dev) / PostgreSQL (production on Render)
- **Static files:** Whitenoise (compressed, manifest-based, 1-year cache)
- **Images:** Cloudinary CDN with auto-resize thumbnails
- **Auth:** django-allauth (email + Google OAuth)
- **Maps:** Leaflet + OpenStreetMap (no API key)
- **Deployment:** Render (free tier), GitHub Actions (keep-alive + status checks)
- **Error tracking:** Sentry
- **CDN:** Cloudflare (optional, at DNS level)

---

## Security

- All secrets loaded from `.env` — never hardcoded
- `.env` and `db.sqlite3` in `.gitignore`
- Admin panel protected by `@staff_member_required`
- Curation endpoints require staff access
- Sentry DSN and Google OAuth credentials are env-only
- HSTS headers enforced
- CSRF protection on all mutation endpoints
- Password minimum length: 8 characters

---

## Key Decisions

- Database (`db.sqlite3`) is gitignored — seed data lives in `fixtures/seed_data.json`
- Email validation runs all services in parallel; any "invalid" rejects immediately
- Verification email is NEVER auto-sent (prevents bounces)
- Messaging uses polling (not WebSockets) — simpler deployment
- Themes use CSS custom properties with session storage
- Maps use Leaflet — no API key, completely free
- All API keys sourced from `.env` only; no hardcoded secrets
