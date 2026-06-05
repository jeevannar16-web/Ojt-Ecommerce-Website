from django.contrib import admin
from .models import Product, CartItem, Order, OrderItem, Category, FavoriteItem, NewsletterSubscriber

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    list_editable = ['status']  # 👈 change status directly from list
    inlines = [OrderItemInline]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'stock', 'rating', 'is_featured', 'is_sale']
    list_editable = ['rating', 'is_featured', 'is_sale']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']

admin.site.register(CartItem)
admin.site.register(FavoriteItem)
admin.site.register(NewsletterSubscriber)