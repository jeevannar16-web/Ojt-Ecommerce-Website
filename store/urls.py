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




    

]