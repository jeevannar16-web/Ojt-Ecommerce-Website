from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
   
  
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('products/', views.product_list, name='product_list'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),

    
path('sale/', views.sale_catalog, name='sale_catalog'),
]


