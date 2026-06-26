"""Re-exports all view functions so `from store.views import ...` works cleanly."""

# ════════════════════════════════════════════════════════════════
# STORE VIEWS MODULE - RE-EXPORTS
# ════════════════════════════════════════════════════════════════
# Re-exports all store views for backward compatibility
# Modular view structure split from monolithic store/views.py

from .cart_views import add_to_cart, cart_view, update_cart_quantity, cart_batch_delete, cart_mini_api
from .checkout_views import checkout_view
from .product_views import product_list, product_detail, product_list_api, product_stock_api, sale_catalog, search_suggestions
from .order_views import order_history_view, cancel_order
from .favorite_views import toggle_favorite, favorites_list
from .curation_views import curation_workspace, update_curation_asset
from .category_curation_views import category_curation_workspace, update_category_asset
from .newsletter_views import newsletter_subscribe, newsletter_unsubscribe
from .review_views import submit_review
