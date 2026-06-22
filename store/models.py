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


class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sizes')
    size = models.CharField(max_length=50, help_text="e.g. S, M, L, XL or 5kg, 10kg")
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product', 'size')

    def __str__(self):
        return f"{self.product.name} - {self.size} ({self.stock})"


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
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.order_number if self.order_number else 'No Number'}"


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


class FavoriteItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} favorited {self.product.name}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True, max_length=254)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


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
