"""URL routing for the store app."""

from django.urls import path
from . import views
from . import seller_views
from . import admin_dashboard_views
from .views import messaging_views

app_name = 'store'


urlpatterns = [
    path('admin-dashboard/', admin_dashboard_views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/activity-log/', admin_dashboard_views.admin_activity_log, name='admin_activity_log'),
    path('admin-dashboard/favorites/', admin_dashboard_views.admin_favorites, name='admin_favorites'),
    path('admin-dashboard/cart/', admin_dashboard_views.admin_cart, name='admin_cart'),
    path('admin-dashboard/sellers/', admin_dashboard_views.admin_sellers, name='admin_sellers'),
    path('admin-dashboard/sellers/<int:seller_id>/', admin_dashboard_views.admin_seller_detail, name='admin_seller_detail'),
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

    # Newsletter & Orders
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('orders/', views.order_history_view, name='order_history'),
    path('orders/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('products/<int:product_id>/review/', views.submit_review, name='submit_review'),

    # ==============================================================================
    path('curation/', views.curation_workspace, name='curation_workspace'),
    path('curation/update-asset/', views.update_curation_asset, name='update_curation_asset'),
    path('curation/category/', views.category_curation_workspace, name='category_curation_workspace'),
    path('curation/category/update-asset/', views.update_category_asset, name='update_category_asset'),

    # ==============================================================================
    path('seller-center/', seller_views.seller_center, name='seller_center'),
    path('seller/apply/', seller_views.seller_apply, name='seller_apply'),
    path('seller/store/<slug:slug>/', seller_views.seller_storefront, name='seller_storefront'),

    # ==============================================================================
    path('seller/', seller_views.seller_dashboard, name='seller_dashboard'),
    path('seller/products/', seller_views.seller_product_list, name='seller_product_list'),
    path('seller/products/add/', seller_views.seller_product_add, name='seller_product_add'),
    path('seller/products/<int:product_id>/edit/', seller_views.seller_product_edit, name='seller_product_edit'),
    path('seller/products/<int:product_id>/delete/', seller_views.seller_product_delete, name='seller_product_delete'),
    path('seller/orders/', seller_views.seller_orders, name='seller_orders'),

    # ==============================================================================
    path('messages/', messaging_views.conversation_list, name='messages_list'),
    path('messages/<int:conversation_id>/', messaging_views.conversation_detail, name='conversation_detail'),
    path('messages/start/<int:product_id>/', messaging_views.start_conversation, name='start_conversation'),
    path('messages/contact-admin/', messaging_views.contact_admin, name='contact_admin'),
    path('api/messages/unread/', messaging_views.api_unread_count, name='api_unread_count'),
    path('api/messages/<int:conversation_id>/new/', messaging_views.api_new_messages, name='api_new_messages'),
    path('api/messages/edit/', messaging_views.api_edit_message, name='api_edit_message'),
    path('api/messages/react/', messaging_views.api_react_message, name='api_react_message'),
    path('api/messages/<int:conversation_id>/reactions/', messaging_views.api_reaction_updates, name='api_reaction_updates'),
    path('api/messages/upload-image/', messaging_views.api_upload_image, name='api_upload_image'),
    path('api/messages/pin/', messaging_views.api_pin_message, name='api_pin_message'),
    path('api/messages/<int:conversation_id>/search/', messaging_views.api_search_messages, name='api_search_messages'),
    path('api/messages/mute/', messaging_views.api_mute_conversation, name='api_mute_conversation'),
    path('api/messages/theme/', messaging_views.api_change_theme, name='api_change_theme'),
    path('api/messages/upload-file/', messaging_views.api_upload_file, name='api_upload_file'),
    path('api/messages/delete/', messaging_views.api_delete_message, name='api_delete_message'),
    path('api/messages/report/', messaging_views.api_report_message, name='api_report_message'),
    path('api/messages/heartbeat/', messaging_views.api_heartbeat, name='api_heartbeat'),
    path('api/messages/online-status/', messaging_views.api_online_status, name='api_online_status'),
    path('api/messages/user-info/', messaging_views.api_user_info, name='api_user_info'),
    path('api/messages/start-call/', messaging_views.api_start_call, name='api_start_call'),
    path('api/messages/update-status/', messaging_views.api_update_status, name='api_update_status'),
    path('api/messages/mark-read/', messaging_views.api_mark_read, name='api_mark_read'),
    path('api/messages/delete-conversation/', messaging_views.api_delete_conversation, name='api_delete_conversation'),
    path('messages/<int:conversation_id>/block/', messaging_views.block_user, name='block_user'),

    # ==============================================================================
    # SECTION: Newsletter — Unsubscribe, Broadcast, Manage
    # ==============================================================================
    path('newsletter/unsubscribe/<str:token>/', views.newsletter_unsubscribe, name='newsletter_unsubscribe'),
    path('admin-dashboard/newsletter/broadcast/', admin_dashboard_views.admin_newsletter_broadcast, name='admin_newsletter_broadcast'),
    path('admin-dashboard/newsletter/subscribers/', admin_dashboard_views.admin_manage_subscribers, name='admin_manage_subscribers'),
]