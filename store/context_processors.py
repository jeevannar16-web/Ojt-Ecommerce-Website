from .models import FavoriteItem, CartItem, Product 
from .models import Category
from django.db.models import Sum

def cart_and_wishlist_counts(request):
    if request.user.is_authenticated:
        # Fetch the product IDs that the user has added to their wishlist
        favorited_ids = FavoriteItem.objects.filter(user=request.user).values_list('product_id', flat=True)
        
        return {
            'global_favorited_ids': list(favorited_ids),
            'wishlist_count': len(favorited_ids),
            'cart_count': CartItem.objects.filter(user=request.user).count()
        }
    
    return {
        'global_favorited_ids': [],
        'wishlist_count': 0,
        'cart_count': 0
    }









def category_list_processor(request):
    """
    Dynamically finds unique categories that actually contain products 
    and sends them to every template automatically.
    """
    # Extract unique categories present across active product instances
    products_with_categories = Product.objects.select_related('category').filter(category__isnull=False)
    
    # Extract distinct categories safely
    unique_categories = []
    seen_ids = set()
    for prod in products_with_categories:
        if prod.category.id not in seen_ids:
            seen_ids.add(prod.category.id)
            unique_categories.append(prod.category)
            
    return {
        'global_categories': unique_categories
    }



def cart_counter(request):
    """Calculates global item quantities by looking directly at CartItem rows."""
    cart_count = 0
    if request.user.is_authenticated:
        # Sum the quantities of all active cart rows for the current user
        user_items = CartItem.objects.filter(user=request.user)
        cart_count = sum(item.quantity for item in user_items)
        
    return {
        'cart_count': cart_count
    }





def global_context(request):
    global_categories = Category.objects.all()

    cart_count = 0
    global_favorited_ids = []

    if request.user.is_authenticated:
        cart_count = CartItem.objects.filter(
            user=request.user
        ).aggregate(total=Sum('quantity'))['total'] or 0

        global_favorited_ids = list(
            FavoriteItem.objects.filter(
                user=request.user
            ).values_list('product_id', flat=True)
        )

    return {
        'global_categories': global_categories,
        'cart_count': cart_count,
        'global_favorited_ids': global_favorited_ids,
    }