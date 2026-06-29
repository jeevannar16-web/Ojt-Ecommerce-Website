"""Favorites and wishlist views."""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import json
from ..models import Product, FavoriteItem
from ..activity_logger import log_action


# FAVORITES / WISHLIST MANAGEMENT
def toggle_favorite(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Please sign in to manage your wishlist.'
        }, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)

    product = get_object_or_404(Product, id=product_id)
    favorite = FavoriteItem.objects.filter(user=request.user, product=product)

    if favorite.exists():
        favorite.delete()
        action = 'removed'
        log_action(request.user, 'fav_remove', f"Removed {product.name} from favorites",
                   {'product_id': product.id, 'product_name': product.name}, request)
    else:
        FavoriteItem.objects.create(user=request.user, product=product)
        action = 'added'
        log_action(request.user, 'fav_add', f"Added {product.name} to favorites",
                   {'product_id': product.id, 'product_name': product.name}, request)

    total_favorites = FavoriteItem.objects.filter(user=request.user).count()
    return JsonResponse({
        'success': True,
        'action': action,
        'total_favorites': total_favorites
    })



@login_required(login_url='/users/login/')
def favorites_list(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            favorite_item = FavoriteItem.objects.filter(user=request.user, product_id=product_id)
            if favorite_item.exists():
                favorite_item.delete()
            total_favorites = FavoriteItem.objects.filter(user=request.user).count()
            return JsonResponse({'status': 'deleted', 'total_favorites': total_favorites})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    favorite_items = FavoriteItem.objects.filter(user=request.user)
    return render(request, 'store/favorites.html', {'favorite_items': favorite_items})
