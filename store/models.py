"""Database models for the store — products, categories, orders, cart items, reviews, and everything in between."""

import mimetypes

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.utils.deconstruct import deconstructible


@deconstructible
class _UploadToPath:
    def __init__(self, prefix, subfolder_attr=None):
        self.prefix = prefix
        self.subfolder_attr = subfolder_attr

    def __call__(self, instance, filename):
        ext = filename.rsplit('.', 1)[-1] if '.' in filename else ''
        name = slugify(instance.name)[:50] or 'image'
        sub = getattr(instance, self.subfolder_attr, None) if self.subfolder_attr else None
        if sub is not None:
            sub_slug = slugify(str(sub))[:50]
            return f'{self.prefix}/{sub_slug}/{name}.{ext}'
        return f'{self.prefix}/{name}.{ext}'


product_image_path = _UploadToPath('products', subfolder_attr='category')
category_image_path = _UploadToPath('category_images')


# ==============================================================================
# SECTION: Category Model
# ==============================================================================

class Category(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to=category_image_path, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and self.image:
            image_file = self.image
            self.image = None
            super().save(*args, **kwargs)
            self.image = image_file
        super().save(*args, **kwargs)


# ==============================================================================
# SECTION: Product Model
# ==============================================================================

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products', null=True, blank=True, help_text="The seller who owns this product")
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to=product_image_path, blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    is_sale = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    size = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Comma-separated sizes, e.g. S,M,L,XL or 5kg,10kg,20kg"
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Original price before discount. Leave blank if same as price.")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and self.image:
            image_file = self.image
            self.image = None
            super().save(*args, **kwargs)
            self.image = image_file
        super().save(*args, **kwargs)

    @property
    def has_sizes(self):
        return self.sizes.exists()

    @property
    def discount_percent(self):
        if self.original_price and self.original_price > self.price:
            return int((1 - self.price / self.original_price) * 100)
        return 0


# ==============================================================================
# SECTION: ProductSize Model
# ==============================================================================

class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sizes')
    size = models.CharField(max_length=50, help_text="e.g. S, M, L, XL or 5kg, 10kg")
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product', 'size')

    def __str__(self):
        return f"{self.product.name} - {self.size} ({self.stock})"


# ==============================================================================
# SECTION: CartItem Model
# ==============================================================================

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=50, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        label = f"{self.quantity} x {self.product.name}"
        if self.size:
            label += f" ({self.size})"
        label += f" ({self.user.username})"
        return label

    @property
    def total_price(self):
        return self.product.price * self.quantity


# ==============================================================================
# SECTION: Order Model
# ==============================================================================

class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Order Placed'),
        ('Processing', 'Preparing'),
        ('Shipped', 'In Transit'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    shipping_address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Delivery latitude from map picker")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Delivery longitude from map picker")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.order_number if self.order_number else 'No Number'}"


# ==============================================================================
# SECTION: OrderItem Model
# ==============================================================================

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    size = models.CharField(max_length=50, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        label = f"{self.quantity} x {self.product.name if self.product else 'Deleted Item'}"
        if self.size:
            label += f" ({self.size})"
        return label


# ==============================================================================
# SECTION: FavoriteItem Model
# ==============================================================================

class FavoriteItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} favorited {self.product.name}"


# ==============================================================================
# SECTION: NewsletterSubscriber Model
# ==============================================================================

class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True, max_length=254)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True, help_text="Is this subscriber still active?")
    token = models.CharField(max_length=64, unique=True, blank=True, null=True, help_text="Unique token for unsubscribe")

    def save(self, *args, **kwargs):
        import uuid
        if not self.token:
            self.token = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.email} ({'active' if self.active else 'inactive'})"


# ==============================================================================
# SECTION: ActivityLog Model
# ==============================================================================

class ActivityLog(models.Model):
    ACTION_TYPES = [
        ('fav_add', 'Added to Favorites'),
        ('fav_remove', 'Removed from Favorites'),
        ('cart_add', 'Added to Cart'),
        ('cart_remove', 'Removed from Cart'),
        ('cart_update', 'Updated Cart Quantity'),
        ('order_place', 'Placed Order'),
        ('order_cancel', 'Cancelled Order'),
        ('order_status', 'Order Status Changed'),
        ('product_create', 'Created Product'),
        ('product_update', 'Updated Product'),
        ('product_delete', 'Deleted Product'),
        ('seller_apply', 'Applied as Seller'),
        ('seller_approve', 'Seller Approved'),
        ('seller_decline', 'Seller Declined'),
        ('seller_revoke', 'Seller Revoked'),
        ('user_register', 'User Registered'),
        ('review_add', 'Added Review'),
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('size_create', 'Size Created'),
        ('size_update', 'Size Updated'),
        ('size_delete', 'Size Deleted'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    description = models.TextField(blank=True)
    details = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Activity logs"

    def __str__(self):
        username = self.user.username if self.user else 'Anonymous'
        return f"{username} — {self.get_action_type_display()} ({self.created_at})"


# ==============================================================================
# SECTION: Review Model
# ==============================================================================

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} — {self.product.name} ({self.rating}★)"


# ==============================================================================
# SECTION: UserOnline Model
# ==============================================================================

class UserOnline(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='online_status')
    last_seen = models.DateTimeField(auto_now=True)
    is_online = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} {'online' if self.is_online else 'offline'}'"


# ==============================================================================
# SECTION: Conversation Model
# ==============================================================================

class Conversation(models.Model):
    THEME_CHOICES = [
        ('dark', 'Dark'),
        ('light', 'Light'),
        ('gold', 'Gold'),
        ('ocean', 'Ocean'),
        ('purple', 'Purple'),
        ('fifa', 'FIFA'),
        ('cricket', 'Cricket'),
        ('anime', 'Anime'),
        ('dev', 'Dev'),
        ('spiderman', 'Spiderman'),
        ('batman', 'Batman'),
        ('ironman', 'Iron Man'),
        ('naruto', 'Naruto'),
        ('goku', 'Goku'),
        ('onepiece', 'One Piece'),
    ]
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_as_customer')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_as_seller')
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(max_length=255, blank=True)
    is_admin_conversation = models.BooleanField(default=False)
    is_muted = models.BooleanField(default=False)
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='dark')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.customer.username} ↔ {self.seller.username} #{self.id}"

    def last_message(self):
        return self.messages.order_by('-created_at').first()

    def unread_count(self, user):
        return self.messages.filter(is_read=False).exclude(sender=user).count()

    def other_user(self, user):
        if user == self.customer:
            return self.seller
        return self.customer


# ==============================================================================
# SECTION: Message Model
# ==============================================================================

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    image = models.ImageField(upload_to='chat_images/%Y/%m/%d/', null=True, blank=True)
    reactions = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_delivered = models.BooleanField(default=False)
    edited = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    file = models.FileField(upload_to='chat_files/%Y/%m/%d/', null=True, blank=True)
    file_type = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['created_at']

    @property
    def mime_type(self):
        if not self.file:
            return None
        mt, _ = mimetypes.guess_type(self.file.name)
        return mt or 'application/octet-stream'

    def __str__(self):
        return f"[{self.created_at:%H:%M}] {self.sender.username}: {self.content[:50]}"


# ==============================================================================
# SECTION: BlockedUser Model
# ==============================================================================

class BlockedUser(models.Model):
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_users')
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_by')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=500, blank=True)

    class Meta:
        unique_together = ('blocker', 'blocked')

    def __str__(self):
        return f"{self.blocker.username} blocked {self.blocked.username}"


# ==============================================================================
# SECTION: MessageReport Model
# ==============================================================================

class MessageReport(models.Model):
    REASON_CHOICES = [
        ('spam', 'Spam'),
        ('harassment', 'Harassment'),
        ('inappropriate', 'Inappropriate Content'),
        ('scam', 'Scam / Fraud'),
        ('other', 'Other'),
    ]
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Report #{self.id} by {self.reported_by.username} ({self.reason})"
