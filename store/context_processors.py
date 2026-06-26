# ==============================================================================
# Module: store.context_processors
# Description: Global template context processors
# ==============================================================================

from .models import Product, Category, FavoriteItem, CartItem
from django.db.models import Sum


# ==============================================================================
# SECTION: Global Context
# ==============================================================================

def global_context(request):
    categories = Category.objects.all()
    cart_count = 0
    favorited_ids = []

    if request.user.is_authenticated:
        cart_count = CartItem.objects.filter(
            user=request.user
        ).aggregate(total=Sum('quantity'))['total'] or 0
        favorited_ids = list(
            FavoriteItem.objects.filter(
                user=request.user
            ).values_list('product_id', flat=True)
        )

    return {
        'global_categories': categories,
        'cart_count': cart_count,
        'global_favorited_ids': favorited_ids,
    }
