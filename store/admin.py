from django.contrib import admin
from .models import Product, CartItem, Order, OrderItem, Category # 💡 Category is imported!

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    inlines = [OrderItemInline]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # 💡 Kept your awesome list layout
    list_display = ['name', 'price', 'stock', 'is_featured']
    # 🚫 REMOVED: prepopulated_fields line that was causing the server crash!

# 💡 REGISTER YOUR NEW CATEGORY MODEL HERE:
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']

# Register your shopping carts
admin.site.register(CartItem)