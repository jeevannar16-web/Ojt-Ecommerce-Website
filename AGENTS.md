# Session Summary

## Goal
Complete full e-commerce platform with admin dashboard, seller marketplace, professional auth/profile, ProductSize inventory, secure role-based access, email validation, credential history, and real-time maps location configuration — all without data loss.

## Constraints & Preferences
- No data dump/reload required — everything works with existing database
- Sellers need admin verification with rejection reasons
- Signup/login pages must look distinct and professional
- Profile must be ecommerce-style (address/phone, not fitness metrics)
- Size selection must be strict per product via ProductSize model
- Favorites must work reliably for all authenticated users
- Admin dashboard must be realistic, secure, and accessible only to staff
- Seller dashboard should resemble a real marketplace (Daraz-style)
- Even when deployed, admin routes must not be easy to access
- `@staff_member_required` on admin dashboard — requires `is_staff=True`
- Admin dashboard link in user dropdown only appears for superusers
- Invalid/unknown emails must be detected at signup (not after sending) — no bounce emails to admin's personal inbox
- Verification flow must be user-initiated (not auto-send)
- Credential history: previously saved inputs shown as clickable suggestions on seller apply page

## Progress

### Done
- Extracted all inline CSS from base.html into 10 files under `static/css/base/`
- Extracted all inline JS from base.html into 6 files under `static/js/base/`
- Created 7 reusable include templates under `templates/includes/`
- Rewrote `templates/layout/base.html` from ~1514 lines to clean includes
- Extracted page-level CSS+JS into `static/css/pages/` and `static/js/pages/`
- Split monolithic `store/views.py` (953 lines) into module package `store/views/` with 9 modules
- Deleted unused apps (`inspiration`, `exercises`)
- Added `Product.seller` (FK User), `Product.created_at`, `ProductSize`, `CartItem.size`, `OrderItem.size` with migrations
- Added `Profile.is_seller`, `seller_requested`, `seller_rejection_reason`, `phone`, address fields, business credential fields with migrations
- Created `store/seller_views.py` (full CRUD dashboard) and `store/admin_dashboard_views.py` (`@staff_member_required`)
- Admin dashboard: sidebar layout, stats row (7+ metrics), order management, pending seller approve/decline/reason, low stock, sellers, favorites, cart, activity log
- Seller dashboard: Daraz-style sidebar, 8 quick-stat cards, top selling products, revenue bars, performance summary, recent orders/products
- Profile: 4-tab layout (Account, Orders, Wishlist, Seller) with seller rejection reason + "Request Again"
- Register: gradient-border with "Become a Seller" checkbox
- Login: clean minimal design, distinct from register
- CSRF hidden token in base.html fixes AJAX favorites toggle
- ActivityLog model with admin log viewer (filters: action type, username, date range)
- Realistic seed data: `seed_realistic.py` — 6 sellers, 50 users, 446 products, 148 orders, 289 favorites, 93 cart items, 106 reviews
- Email verification system with `django.contrib.sites`, OTP codes, user-initiated "Send Code" button
- Email validation (`verification/email_validator.py`): runs ALL services — if ANY says invalid → rejected
  - **Check-Mail.org** (1,000 free/month) — API key: `cmapi_6e646751af42e768896bf757e4440ea4275d609b1e3f1a07`
  - **MyEmailVerifier** (100 free/day) — API key: `qiRKOoTHih7UcmAh`
  - **ZeroBounce** (100 free/month) — no key set yet, skipped
  - **NeverBounce** — emptied (trial expired)
  - DNS MX fallback via `dnspython`
- Fixed MyEmailVerifier API URL (`client.myemailverifier.com/verifier/validate_single/{email}/{key}` — GET)
- Fixed Check-Mail API URL (`api.check-mail.org/v1/check` — GET with params)
- `validate_email_deliverability()` now runs all services; any "invalid" response rejects immediately
- Created `CredentialHistory` model (FK User, stores store_name, business_type, store_description, business_registration, tax_id, business_address, phone, created_at)
- Migration `users.0009_credential_history` applied
- Seller apply page shows last 5 credential sets as clickable cards → fills form fields via JS → user can edit
- **Multi-language translation system (Nepali, Hindi, Korean, English)**
  - Custom DB-backed Translation model with `|t` filter (auto-loaded in all templates)
  - LanguageMiddleware detects `?lang=` query param
  - `available_languages` context processor injects all active languages for nav switcher
  - Created `seed_translations` management command using `deep-translator` (MyMemory API preferred, falls back to Google scraping)
  - Added `|t` filter to **30 template files** (all user-facing pages translated)
  - **613 translation keys** extracted (**576 from templates + 37 from Python views**)
  - **~680 translations per language** seeded
  - Language switcher dropdown in header nav
  - `messages.html` uses `{{ message|t }}` so flash messages auto-translate
  - `seed_translations` auto-scans both `.html`/`.txt` and `.py` files for translatable strings
  - Future: just add `|t` in templates or `messages.*()` in views, then re-run `seed_translations`
- **Auto-currency conversion** — prices auto-convert based on language:
  - English → USD ($), Nepali → NPR (रु), Hindi → INR (₹), Korean → KRW (₩)
  - `|currency` filter globally available (no `{% load %}` needed)
  - Fetches live rates from `open.er-api.com` (free, no key, no credit card) with 1-hour cache
  - `localization/currency.py`: exchange rate service with JSON file caching
  - 37+ template price displays updated to use `{{ price|currency }}`
- **Location map** in footer using Leaflet + OpenStreetMap (free, no API key)
  - `static/js/base/map.js` initializes map centered on Kathmandu, Nepal
  - Leaflet CDN loaded in `base.html`
  - `templates/includes/footer.html` — Col 5 with map + address

## What Works (added this session)
- **Checkout map picker**: click to place draggable marker, reverse geocode (Nominatim) auto-fills address, "Use My Location" (browser geolocation), location search box
- **"Deliver to Home" button** on checkout: one-click fills all address fields + places marker from saved profile lat/lng
- **Profile map picker**: set default delivery location from Account tab
- **Order history maps**: collapsible "View Delivery Location" toggle on each order card shows a 180px map with delivery marker
- **Footer map**: dynamically shows logged-in user's home location (falls back to Kathmandu, Nepal)
- **Header delivery badge**: shows user's saved city with geo icon (links to profile edit)
- **Homepage delivery card**: "Deliver to" section after hero with address, toggle-able mini map, and edit link
- `Order.latitude` / `Order.longitude` saved per order from map picker
- `Profile.latitude` / `Profile.longitude` saved as default delivery location

### In Progress
- (none)

### Blocked
- (none)

## Key Decisions
- Email validation runs ALL services in parallel order; if any says invalid → reject (stricter than "first result wins")
- Delivery method for sender reputation: MX records supported (better for reputation)
- Verification email is NEVER auto-sent: user clicks "Send Code" — prevents bounces to admin inbox
- NeverBounce key emptied (trial-only, not perpetually free)
- CredentialHistory stores full credential snapshots per submission (not just diff)
- Old fitness fields retained on Profile but excluded from form — no data loss

## What Works
- Registration with optional seller request + email validation
- Login/logout
- Profile editing (ecommerce fields), order history, favorites toggle, seller request/re-request
- Seller CRUD (create/edit/delete products), order viewing, grid listing
- Admin dashboard stats, order status updates, seller approve/decline/reason, revoke seller
- Product size management (comma-separated → ProductSize objects)
- Cart with size selection, checkout with size tracking
- Favorites toggle (CSRF fixed)
- Email validation rejects fake Gmail addresses (hi@gmail.com → caught by MyEmailVerifier)
- Email validation rejects bad domains, accepts real emails (jeevannar16@gmail.com)
- Credential history on seller apply: click to fill, edit, resubmit
- All pages use clean sidebar layout (admin & seller)

## Critical Context
- Django 5.0.6, Python 3.12, SQLite default DB — all running from `./venv/bin/python`
- Apps installed: `users`, `store`, `homepages`
- Admin user "jeevan" is superuser + seller
- 9 migrations applied: `users.0002`–`0009`, `store.0010`–`0012`
- Run `./venv/bin/python manage.py check` to verify no issues
- `.env` has CHECKMAIL_API_KEY and MYEMAILVERIFIER_API_KEY active; NEVERBOUNCE_API_KEY emptied; ZEROBOUNCE_API_KEY empty
- Server runs on `http://localhost:8000`
- Dev server restart command: `pkill -f "manage.py"; nohup ./venv/bin/python manage.py runserver 0.0.0.0:8000 > /tmp/django.log 2>&1 &`
