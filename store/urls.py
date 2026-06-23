from django.urls import path
from . import views
from . import seller_views
from . import admin_dashboard_views

app_name = 'store'

urlpatterns = [
    path('admin-dashboard/', admin_dashboard_views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/activity-log/', admin_dashboard_views.admin_activity_log, name='admin_activity_log'),
    path('admin-dashboard/favorites/', admin_dashboard_views.admin_favorites, name='admin_favorites'),
    path('admin-dashboard/cart/', admin_dashboard_views.admin_cart, name='admin_cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('products/', views.product_list, name='product_list'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('sale/', views.sale_catalog, name='sale_catalog'),
    path('cart/update/<int:product_id>/<str:action>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('cart/batch-delete/', views.cart_batch_delete, name='cart_batch_delete'),
    path('favorites/', views.favorites_list, name='favorites_list'),
    path('favorites/toggle/<int:product_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('search/suggestions/', views.search_suggestions, name='search_suggestions'),
    path('api/products/', views.product_list_api, name='product_list_api'),
    path('api/product-stock/<int:product_id>/', views.product_stock_api, name='product_stock_api'),
    path('api/cart-mini/', views.cart_mini_api, name='cart_mini_api'),

    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('orders/', views.order_history_view, name='order_history'),
    path('orders/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('products/<int:product_id>/review/', views.submit_review, name='submit_review'),

    # Product Curation
    path('curation/', views.curation_workspace, name='curation_workspace'),
    path('curation/update-asset/', views.update_curation_asset, name='update_curation_asset'),
    path('curation/category/', views.category_curation_workspace, name='category_curation_workspace'),
    path('curation/category/update-asset/', views.update_category_asset, name='update_category_asset'),

    # Seller Center (public)
    path('seller-center/', seller_views.seller_center, name='seller_center'),
    path('seller/apply/', seller_views.seller_apply, name='seller_apply'),
    path('seller/store/<slug:slug>/', seller_views.seller_storefront, name='seller_storefront'),

    # Seller Dashboard
    path('seller/', seller_views.seller_dashboard, name='seller_dashboard'),
    path('seller/products/', seller_views.seller_product_list, name='seller_product_list'),
    path('seller/products/add/', seller_views.seller_product_add, name='seller_product_add'),
    path('seller/products/<int:product_id>/edit/', seller_views.seller_product_edit, name='seller_product_edit'),
    path('seller/products/<int:product_id>/delete/', seller_views.seller_product_delete, name='seller_product_delete'),
    path('seller/orders/', seller_views.seller_orders, name='seller_orders'),
]