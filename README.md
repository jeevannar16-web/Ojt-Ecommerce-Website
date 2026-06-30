# Ecommerce Platform

Full-stack Django ecommerce platform with seller marketplace, admin dashboard, real-time maps, multi-language support, email verification, and messaging — built for production use.

---

## What's Inside

### Storefront
- Product catalog with 17 categories, size management via ProductSize model
- Product detail pages with reviews, seller info, and chat button
- Cart with size selection, checkout with map-based delivery location picker
- Order tracking with visual timeline and delivery map
- Favorites/wishlist toggle (CSRF-safe AJAX)
- Flash sales, featured products, curated sections on homepage

### Authentication & Users
- Register/login with distinct professional styling
- Profile with 4 tabs: Account, Orders, Wishlist, Seller
- Email verification (user-initiated OTP — never auto-sent)
- Email validation via Check-Mail.org + MyEmailVerifier + DNS MX fallback
- Password change with email confirmation
- Credential history: saved form inputs as clickable suggestions on seller apply

### Seller Marketplace (Daraz-style)
- Seller application with admin approval/rejection + reason
- Seller dashboard: revenue stats, top products, recent orders, performance summary
- Full product CRUD with image upload and size management
- Order management for seller's own products
- Storefront page per seller
- Contact support via messaging system

### Admin Dashboard
- `@staff_member_required` — only staff can access
- Stats row: total users, products, orders, revenue, pending sellers, low stock, etc.
- Order management with status updates
- Seller approve/decline with rejection reason
- Low stock alerts
- Activity log viewer with filters (action type, user, date range)
- Favorites and cart overview
- Message center with full conversation management

### Messaging System
- Customer ↔ Seller conversations per product
- Seller ↔ Admin support conversations
- Real-time unread badge in floating bubble (polls every 5s)
- Conversation list with search and filter tabs
- Mute/delete conversations

### Maps & Location
- Checkout map picker: draggable marker, reverse geocoding (Nominatim), "Use My Location"
- Profile map picker: set default delivery location
- Order history maps: collapsible delivery location on each order
- Footer map: shows user's saved location (falls back to Kathmandu)
- Header delivery badge: shows saved city
- All powered by Leaflet + OpenStreetMap (free, no API key)

### Multi-Language & Currency
- Custom DB-backed Translation model with `|t` filter
- Languages: English, Nepali, Hindi, Korean
- Language switcher in header via `?lang=` query param
- `seed_translations` command auto-scans templates and views
- Auto-currency conversion: USD / NPR / INR / KRW via `|currency`
- Live exchange rates from open.er-api.com with 1-hour cache

### Email Verification System
- Validates email deliverability before allowing signup
- Runs multiple services in parallel; any "invalid" rejects immediately
- Check-Mail.org (1000/mo free), MyEmailVerifier (100/day free), DNS MX fallback
- Never auto-sends — user clicks "Send Code" to request OTP

---

## Quick Start

```bash
git clone <repo-url>
cd Ojt-Ecommerce-Website
./start.sh
```

One command creates venv, installs deps, and starts the server on port 8000. The `db.sqlite3` is included — no migrations or seed scripts needed.

Windows: `start.bat`

---

## Project Structure

| Directory | Purpose |
|-----------|---------|
| `store/` | Core app: models, views (split into modules), URLs, templates, admin |
| `users/` | User profiles, authentication forms, credential history |
| `homepages/` | Landing page, static pages (cookies, privacy, terms) |
| `localization/` | Translation system, currency conversion, language middleware |
| `verification/` | Email validation (multi-provider), OTP email sending |
| `templates/` | All HTML templates organized by app and feature |
| `static/` | CSS, JS, images — organized into `base/` and `pages/` |

---

## Key Decisions

- Email validation runs ALL services in parallel; any "invalid" rejects immediately
- Verification email is NEVER auto-sent — prevents bounces to admin's inbox
- Database (`db.sqlite3`) tracked in git so clones include all data
- Admin dashboard protected by `@staff_member_required`
- Product sizes handled via dedicated `ProductSize` model (not free-text)
- Leaflet/OSM for maps — no API key required, completely free
