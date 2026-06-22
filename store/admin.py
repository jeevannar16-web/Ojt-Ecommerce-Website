from django.contrib import admin
from django.utils.html import format_html
from .models import Product, ProductSize, CartItem, Order, OrderItem, Category, FavoriteItem, NewsletterSubscriber, Review


# ════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════
def image_preview(url):
    return format_html(
        '<img src="{}" style="width:60px; height:60px; object-fit:cover; border-radius:6px;" />',
        url
    )


# ════════════════════════════════════════════════════════════════
# ORDER ADMIN
# ════════════════════════════════════════════════════════════════
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_image', 'product', 'quantity', 'price']

    @admin.display(description='Image')
    def product_image(self, obj):
        if obj.product and obj.product.image:
            return image_preview(obj.product.image.url)
        return '—'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_number', 'user', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    list_editable = ['status']
    search_fields = ['order_number', 'user__username', 'user__email']
    readonly_fields = ['order_number', 'created_at']
    inlines = [OrderItemInline]

    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'user', 'status', 'created_at')
        }),
        ('Payment', {
            'fields': ('total_amount',)
        }),
    )


# ════════════════════════════════════════════════════════════════
# PRODUCT SIZE INLINE
# ════════════════════════════════════════════════════════════════
class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1


# ════════════════════════════════════════════════════════════════
# PRODUCT SIZE ADMIN
# ════════════════════════════════════════════════════════════════
@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ['product', 'size', 'stock']
    list_filter = ['product__seller']
    search_fields = ['product__name', 'size']


# ════════════════════════════════════════════════════════════════
# PRODUCT ADMIN  (word-wrap friendly)
# ════════════════════════════════════════════════════════════════
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['image_tag', 'colored_name', 'category', 'seller', 'price', 'stock', 'rating', 'is_featured', 'is_sale']
    list_filter = ['category', 'is_featured', 'is_sale', 'seller']
    list_editable = ['price', 'stock', 'rating', 'is_featured', 'is_sale']
    search_fields = ['name', 'description']
    readonly_fields = ['image_tag']
    list_per_page = 20

    inlines = [ProductSizeInline]

    class Media:
        css = {
            'all': ['css/admin_word_wrap.css']
        }

    @admin.display(description='Image')
    def image_tag(self, obj):
        if obj.image:
            return image_preview(obj.image.url)
        return '—'

    @admin.display(description='Name')
    def colored_name(self, obj):
        if obj.is_sale:
            return format_html('<span style="color:#e74c3c;font-weight:700;">🔥 {}</span>', obj.name[:60])
        return format_html('<span style="max-width:200px;display:inline-block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{}</span>', obj.name[:60])

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'category', 'seller', 'description')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'stock')
        }),
        ('Product Details', {
            'fields': ('image_tag', 'image', 'size', 'rating')
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
    list_display = ['image_tag', 'id', 'name']
    search_fields = ['name']

    @admin.display(description='Image')
    def image_tag(self, obj):
        if obj.image:
            return image_preview(obj.image.url)
        return '—'


# ════════════════════════════════════════════════════════════════
# REVIEW ADMIN
# ════════════════════════════════════════════════════════════════
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product_image', 'product', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['product__name', 'user__username']
    readonly_fields = ['product_image', 'created_at']

    @admin.display(description='Image')
    def product_image(self, obj):
        if obj.product and obj.product.image:
            return image_preview(obj.product.image.url)
        return '—'

    fieldsets = (
        ('Review Info', {
            'fields': ('product_image', 'product', 'user', 'rating', 'created_at')
        }),
        ('Content', {
            'fields': ('comment',)
        }),
    )


# ════════════════════════════════════════════════════════════════
# CART ITEM ADMIN
# ════════════════════════════════════════════════════════════════
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['product_image', 'user', 'product', 'quantity', 'item_total']
    search_fields = ['user__username', 'product__name']
    readonly_fields = ['product_image', 'item_total']

    @admin.display(description='Image')
    def product_image(self, obj):
        if obj.product and obj.product.image:
            return image_preview(obj.product.image.url)
        return '—'

    @admin.display(description='Total')
    def item_total(self, obj):
        if obj.product and obj.quantity:
            return f'${obj.product.price * obj.quantity:.2f}'
        return '—'

    fieldsets = (
        ('Cart Info', {
            'fields': ('product_image', 'user', 'product', 'quantity', 'item_total')
        }),
    )


# ════════════════════════════════════════════════════════════════
# FAVORITE ITEM ADMIN
# ════════════════════════════════════════════════════════════════
@admin.register(FavoriteItem)
class FavoriteItemAdmin(admin.ModelAdmin):
    list_display = ['product_image', 'user', 'product', 'product_price', 'product_category', 'created_at']
    search_fields = ['user__username', 'product__name']
    list_filter = ['product__category', 'created_at']
    readonly_fields = ['product_image', 'product_price', 'product_category', 'created_at']

    @admin.display(description='Image')
    def product_image(self, obj):
        if obj.product and obj.product.image:
            return image_preview(obj.product.image.url)
        return '—'

    @admin.display(description='Price')
    def product_price(self, obj):
        if obj.product:
            return f'${obj.product.price:.2f}'
        return '—'

    @admin.display(description='Category')
    def product_category(self, obj):
        if obj.product:
            return obj.product.category
        return '—'

    fieldsets = (
        ('Favorite Info', {
            'fields': ('product_image', 'user', 'product', 'product_price', 'product_category', 'created_at')
        }),
    )


# ════════════════════════════════════════════════════════════════
# NEWSLETTER SUBSCRIBER ADMIN
# ════════════════════════════════════════════════════════════════
@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email']
    search_fields = ['email']