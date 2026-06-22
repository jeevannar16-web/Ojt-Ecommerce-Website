# Project Structure

```
Ojt-Ecommerce-Website/
├── fitness_hub/                 # Django project configuration
│   ├── settings.py              # App registry, templates, static/media config
│   ├── urls.py                  # Root URL routing to all apps
│   └── wsgi.py
│
├── store/                       # Core ecommerce functionality
│   ├── models.py                # Category, Product, CartItem, Order, OrderItem, FavoriteItem, Review, NewsletterSubscriber
│   ├── admin.py                 # Admin config for Order, Product, Category, Review
│   ├── context_processors.py    # Cart/wishlist counts, categories, cart counter
│   ├── urls.py                  # ~20 URL patterns → all store views
│   ├── templatetags/            # Custom template tags/filters
│   │   └── store_extras.py
│   ├── views/                   # Modular view package (split from monolithic views.py)
│   │   ├── __init__.py          # Re-exports all views for backward compat
│   │   ├── cart_views.py        # add_to_cart, cart_view, update_cart_quantity
│   │   ├── checkout_views.py    # checkout_view
│   │   ├── product_views.py     # product_list, product_detail, product_list_api, sale_catalog, search_suggestions
│   │   ├── order_views.py       # order_history_view, cancel_order
│   │   ├── favorite_views.py    # toggle_favorite, favorites_list
│   │   ├── curation_views.py    # curation_workspace, update_curation_asset
│   │   ├── category_curation_views.py  # category_curation_workspace, update_category_asset
│   │   ├── newsletter_views.py  # newsletter_subscribe
│   │   └── review_views.py      # submit_review
│   └── migrations/
│
├── users/                       # User authentication & profiles
│   ├── models.py                # Profile model
│   ├── views.py                 # login, register, profile
│   └── templates/users/         # login.html, register.html, profile.html, password_reset/
│
├── homepages/                   # Home page & legal pages
│   ├── views.py                 # home, privacy, terms, cookies
│   └── templates/homepages/     # home.html, privacy.html, terms.html, cookies.html
│
├── exercises/                   # Exercise content (separate app)
├── inspiration/                 # Inspiration content (separate app)
│
├── static/                      # Organized static assets
│   ├── css/
│   │   ├── base/                # Base layout styles (loaded on every page)
│   │   │   ├── variables.css    # CSS custom properties (colors, fonts, spacing)
│   │   │   ├── reset.css        # Universal box-sizing, body defaults, noise overlay
│   │   │   ├── scrollbar.css    # WebKit & Firefox scrollbar styling
│   │   │   ├── announcement.css # Top announcement bar + shimmer animation
│   │   │   ├── navigation.css   # Main nav bar, logo, actions, user dropdown
│   │   │   ├── category_nav.css # Scrollable category nav with icons + tooltips
│   │   │   ├── messages.css     # Toast messages, favorite button, cart badge
│   │   │   ├── footer.css       # Full footer (brand, links, newsletter, bottom bar)
│   │   │   ├── back_to_top.css  # Floating back-to-top button with SVG arc
│   │   │   └── search.css       # Search dropdown & suggestion items
│   │   ├── pages/               # Per-page styles
│   │   │   ├── product_list.css # Catalog grid, filters, sort bar, cards, skeleton
│   │   │   ├── product_detail.css # Product detail page, reviews, size picker
│   │   │   ├── checkout.css     # Checkout form, steps, order summary
│   │   │   ├── order_tracking.css # Order tracking dashboard, timeline
│   │   │   └── favorites.css    # Wishlist grid, cards, empty state
│   │   └── admin/               # Admin/curation styles
│   ├── js/
│   │   ├── base/                # Base JS loaded on every page
│   │   │   ├── main.js          # getCookie, showToast, validateSearch, back-to-top
│   │   │   ├── cart.js          # addToCart function
│   │   │   ├── favorites.js     # toggleFavorite function
│   │   │   ├── navigation.js    # Category nav scroll, drag, keyboard
│   │   │   ├── search.js        # Live search dropdown, history, suggestions
│   │   │   └── newsletter.js    # Newsletter AJAX subscription
│   │   ├── pages/               # Per-page JS
│   │   │   ├── product_list.js  # Infinite scroll with IntersectionObserver
│   │   │   ├── product_detail.js # Size selector, qty picker, review submission
│   │   │   ├── checkout.js      # Payment/delivery option selection, form submit
│   │   │   └── favorites.js     # AJAX remove with smooth fade-out animation
│   │   └── admin/               # Admin/curation JS
│   └── images/
│
├── templates/                   # Django templates
│   ├── layout/
│   │   └── base.html            # Base template (uses includes + external CSS/JS)
│   ├── includes/                # Reusable template fragments
│   │   ├── announcement_bar.html
│   │   ├── header.html          # Logo, search, nav actions, user dropdown
│   │   ├── category_nav.html    # Scrollable category navigation
│   │   ├── messages.html        # Toast messages with auto-dismiss
│   │   ├── footer.html          # Full footer with newsletter
│   │   ├── back_to_top.html     # Back-to-top button
│   │   └── toast_container.html
│   ├── partials/                # Reusable component partials
│   │   ├── product_card.html
│   │   └── star_rating.html
│   ├── store/                   # Store page templates
│   │   ├── product_list.html
│   │   ├── product_detail.html
│   │   ├── cart.html
│   │   ├── checkout.html
│   │   ├── order_tracking.html
│   │   ├── favorites.html
│   │   ├── curation.html
│   │   └── curation_category.html
│   ├── users/                   # User auth templates
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── profile.html
│   │   └── password_reset/
│   ├── homepages/               # Home & legal pages
│   └── exercises/               # Exercise content pages
│
└── PROJECT_STRUCTURE.md         # This file
```
