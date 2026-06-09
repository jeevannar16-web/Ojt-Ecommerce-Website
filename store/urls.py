from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    # Remove any spaces within these strings!
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),  # 💡 Ensure this says 'cart/' NOT ' cart/'
    path('checkout/', views.checkout_view, name='checkout'),
    path('products/', views.product_list, name='product_list'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('sale/', views.sale_catalog, name='sale_catalog'),
    path('cart/update/<int:product_id>/<str:action>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('favorites/', views.favorites_list, name='favorites_list'),
    path('favorites/toggle/<int:product_id>/', views.toggle_favorite, name='toggle_favorite'),

    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('orders/', views.order_history_view, name='order_history'),



    path('orders/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('products/<int:product_id>/review/', views.submit_review, name='submit_review'),



# 1. The main frontend layout dashboard workspace route
    path('curation/', views.curation_workspace, name='curation_workspace'),
    
    # 2. Ensure your handling endpoint route matches your HTML form action
    path('curation/update-asset/', views.update_curation_asset, name='update_curation_asset'),
    path('curation/category/', views.category_curation_workspace, name='category_curation_workspace'),
    path('curation/category/update-asset/', views.update_category_asset, name='update_category_asset'),


]