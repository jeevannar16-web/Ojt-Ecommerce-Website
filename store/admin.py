from django.contrib import admin
from .models import Product, CartItem, Order, OrderItem, Category, FavoriteItem, NewsletterSubscriber, Review

# ════════════════════════════════════════════════════════════════
# ORDER ADMIN
# ════════════════════════════════════════════════════════════════
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    list_editable = ['status']
    inlines = [OrderItemInline]
    readonly_fields = ['order_number', 'created_at']


# ════════════════════════════════════════════════════════════════
# PRODUCT ADMIN
# ════════════════════════════════════════════════════════════════
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'rating', 'is_featured', 'is_sale']
    list_filter = ['category', 'is_featured', 'is_sale']
    list_editable = ['rating', 'is_featured', 'is_sale']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'category', 'description')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'stock')
        }),
        ('Product Details', {
            'fields': ('image', 'size', 'rating')
        }),
        ('Status', {
            'fields': ('is_featured', 'is_sale')
        }),
    )


# ════════════════════════════════════════════════════════════════
# CATEGORY ADMIN
# ════════════════════════════════════════════════════════════════
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']


# ════════════════════════════════════════════════════════════════
# REVIEW ADMIN
# ════════════════════════════════════════════════════════════════
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['product__name', 'user__username']
    readonly_fields = ['created_at']


# ════════════════════════════════════════════════════════════════
# CART ITEM ADMIN
# ════════════════════════════════════════════════════════════════
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'quantity']
    search_fields = ['user__username', 'product__name']


# ════════════════════════════════════════════════════════════════
# FAVORITE ITEM ADMIN
# ════════════════════════════════════════════════════════════════
@admin.register(FavoriteItem)
class FavoriteItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    search_fields = ['user__username', 'product__name']
    readonly_fields = ['created_at']


# ════════════════════════════════════════════════════════════════
# NEWSLETTER SUBSCRIBER ADMIN (NO created_at)
# ════════════════════════════════════════════════════════════════
@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email']
    search_fields = ['email']