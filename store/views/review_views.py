from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import json
from ..models import Product, Review, OrderItem
from ..activity_logger import log_action
from django.db.models import Avg


@login_required
def submit_review(request, product_id):
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=400)

    product = get_object_or_404(Product, id=product_id)

    has_purchased = OrderItem.objects.filter(
        order__user=request.user,
        order__status='Delivered',
        product=product
    ).exists()

    if not has_purchased:
        return JsonResponse({
            'success': False,
            'message': 'You can only review products from delivered orders.'
        })

    data = json.loads(request.body)
    rating = int(data.get('rating', 0))
    comment = data.get('comment', '').strip()

    if not 1 <= rating <= 5:
        return JsonResponse({'success': False, 'message': 'Invalid rating.'})

    review, created = Review.objects.update_or_create(
        user=request.user,
        product=product,
        defaults={'rating': rating, 'comment': comment}
    )

    avg = Review.objects.filter(product=product).aggregate(Avg('rating'))['rating__avg']
    product.rating = round(avg, 1)
    product.save()

    log_action(request.user, 'review_add', f"Reviewed {product.name} ({rating}★)",
               {'product_id': product.id, 'product_name': product.name, 'rating': rating, 'created': created}, request)

    total_reviews = Review.objects.filter(product=product).count()

    return JsonResponse({
        'success': True,
        'message': 'Review submitted successfully!',
        'new_rating': float(product.rating),
        'total_reviews': total_reviews,
        'created': created
    })
