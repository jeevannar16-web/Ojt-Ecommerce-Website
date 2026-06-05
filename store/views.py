from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
import json
from django.views.decorators.csrf import csrf_protect
from .models import Category, Product, CartItem, Order, OrderItem, FavoriteItem, NewsletterSubscriber
from django.db import IntegrityError
import re 
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Avg

from .models import Review


# =====================================================================
# 1. ADD TO CART
# =====================================================================
def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'requires_login': True,
            'message': 'Please sign in to add items to your bag.'
        }, status=401)

    product = get_object_or_404(Product, id=product_id)

    if product.stock <= 0:
        return JsonResponse({
            'success': False,
            'message': 'This item is out of stock!'
        })

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={'quantity': 1}
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    # Decrease stock when added to cart
    product.stock -= 1
    product.save()

    total_cart_items = CartItem.objects.filter(
        user=request.user
    ).aggregate(total=Sum('quantity'))['total'] or 0

    return JsonResponse({
        'success': True,
        'message': f'{product.name} added to your bag!',
        'cart_count': total_cart_items,
        'new_stock': product.stock
    })

# =====================================================================
# 2. CART VIEW
# =====================================================================
def cart_view(request):
    cart_items = []
    subtotal = 0.0

    if request.user.is_authenticated:
        db_items = CartItem.objects.filter(user=request.user)
        for item in db_items:
            item_total = float(item.product.price) * int(item.quantity)
            subtotal += item_total
            cart_items.append({
                'product': item.product,
                'quantity': item.quantity,
                'total_price': item_total,
                'id': item.id
            })
    else:
        session_cart = request.session.get('cart', {})
        for product_id, quantity in session_cart.items():
            try:
                product = Product.objects.get(id=int(product_id))
                item_total = float(product.price) * int(quantity)
                subtotal += item_total
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'total_price': item_total,
                    'id': product.id
                })
            except Product.DoesNotExist:
                continue

    promo_code = request.GET.get('promo_code', '').strip().upper()
    promo_applied = False
    if promo_code == "FIT-CODEX":
        subtotal = float(subtotal) * 0.80
        promo_applied = True

    context = {
        'cart_items': cart_items,
        'grand_total': round(subtotal, 2),
        'total_amount': round(subtotal, 2),
        'promo_applied': promo_applied,
        'promo_code': promo_code,
    }
    return render(request, 'store/cart.html', context)

# =====================================================================
# 3. UPDATE CART QUANTITY — stock restores on remove/delete
# =====================================================================
def update_cart_quantity(request, product_id, action):
    if request.user.is_authenticated:
        cart_item = get_object_or_404(CartItem, id=product_id, user=request.user)
        product = cart_item.product

        if action == 'add':
            if product.stock > 0:
                cart_item.quantity += 1
                cart_item.save()
                product.stock -= 1
                product.save()
        elif action == 'remove':
            cart_item.quantity -= 1
            product.stock += 1  # restore 1 unit
            product.save()
            if cart_item.quantity <= 0:
                cart_item.delete()
            else:
                cart_item.save()
        elif action == 'delete':
            product.stock += cart_item.quantity  # restore all units
            product.save()
            cart_item.delete()
    else:
        cart = request.session.get('cart', {})
        str_id = str(product_id)
        if str_id in cart:
            if action == 'add':
                cart[str_id] += 1
            elif action == 'remove':
                cart[str_id] -= 1
                if cart[str_id] <= 0:
                    del cart[str_id]
            elif action == 'delete':
                del cart[str_id]
        request.session['cart'] = cart
        request.session.modified = True

    return redirect('store:cart')

# =====================================================================
# 4. CHECKOUT — stock already decreased at cart stage, no change needed
# =====================================================================
@login_required
def checkout_view(request):
    db_items = CartItem.objects.filter(user=request.user)

    if not db_items.exists():
        messages.error(request, "Your cart is empty! Cannot checkout.")
        return redirect('store:cart')

    cart_items = []
    total_amount = 0.0
    for item in db_items:
        item_total = float(item.product.price) * int(item.quantity)
        total_amount += item_total
        cart_items.append({
            'product': item.product,
            'quantity': item.quantity,
            'total_price': item_total
        })

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        shipping_address = request.POST.get('shipping_address')
        city = request.POST.get('city')
        postal_code = request.POST.get('postal_code')

        if not all([full_name, shipping_address, city, phone_number]):
            messages.error(request, "Please fill out all required shipping and credential inputs.")
            return render(request, 'store/checkout.html', {'cart_items': cart_items, 'total_amount': total_amount})

        import uuid
        generated_order_number = uuid.uuid4().hex[:10].upper()

        order = Order.objects.create(
            user=request.user,
            order_number=generated_order_number,
            full_name=full_name,
            email=email,
            shipping_address=f"{shipping_address}, {city} (ZIP: {postal_code})",
            total_amount=total_amount,
            status='Pending'
        )

        for item in db_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.product.price,
                quantity=item.quantity
            )
            # ✅ NO stock change here — already decreased when added to cart

        db_items.delete()
        messages.success(request, f"Thank you! Your fitness order #{order.id} has been placed successfully.")
        return redirect('store:order_history')

    return render(request, 'store/checkout.html', {'cart_items': cart_items, 'total_amount': total_amount})

# =====================================================================
# 5. ORDER HISTORY
# =====================================================================
@login_required
def order_history_view(request):
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    recent_orders = user_orders.filter(status__in=['Delivered', 'Cancelled'])
    upcoming_orders = user_orders.exclude(status__in=['Delivered', 'Cancelled'])
    context = {
        'upcoming_orders': upcoming_orders,
        'recent_orders': recent_orders,
    }
    return render(request, 'store/order_tracking.html', context)

# =====================================================================
# 6. PRODUCT PAGES
# =====================================================================
def product_list(request):
    products = Product.objects.all()
    title = "Our Full Catalog"
    is_search = False

    category_id = request.GET.get('category')
    if category_id:
        try:
            products = products.filter(category_id=int(category_id))
            if products.exists():
                title = f"Elite {products.first().category.name} Collection"
        except (ValueError, TypeError):
            pass

    search_query = request.GET.get('search', '').strip()
    if search_query:
        products = products.filter(name__icontains=search_query)
        title = f'Search Results for "{search_query}"'
        is_search = True

    recommendations = Product.objects.all().order_by('?')[:4]
    context = {
        'products': products,
        'recommendations': recommendations,
        'title': title,
        'is_search': is_search,
    }
    return render(request, 'store/product_list.html', context)

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    recommendations = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:4]
    
    if not recommendations.exists():
        recommendations = Product.objects.exclude(id=product.id)[:4]

    is_favorited = False
    user_review = None
    has_purchased = False

    if request.user.is_authenticated:
        is_favorited = FavoriteItem.objects.filter(
            user=request.user, 
            product=product
        ).exists()
        
        user_review = Review.objects.filter(
            user=request.user, 
            product=product
        ).first()
        
        has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            order__status='Delivered',
            product=product
        ).exists()

    reviews = Review.objects.filter(
        product=product
    ).select_related('user').order_by('-created_at')
    
    total_reviews = reviews.count()

    # calculate rating breakdown (for progress bars)
    rating_breakdown = {}
    for i in range(1, 6):
        count = reviews.filter(rating=i).count()
        percentage = round((count / total_reviews) * 100) if total_reviews > 0 else 0
        rating_breakdown[i] = {
            'count': count,
            'percentage': percentage
        }

    context = {
        'product': product,
        'recommendations': recommendations,
        'is_favorited': is_favorited,
        'reviews': reviews,
        'total_reviews': total_reviews,
        'user_review': user_review,
        'has_purchased': has_purchased,
        'rating_breakdown': rating_breakdown,
    }
    return render(request, 'store/product_detail.html', context)

def sale_catalog(request):
    try:
        products = Product.objects.filter(is_sale=True)
        if not products.exists():
            products = Product.objects.all()
    except Exception:
        products = Product.objects.all()

    recommendations = Product.objects.all().order_by('?')[:4]
    context = {
        'products': products,
        'recommendations': recommendations,
        'title': 'Flash Sale Collection',
        'is_sale_page': True
    }
    return render(request, 'store/product_list.html', context)

# =====================================================================
# 7. FAVORITES
# =====================================================================
@login_required
def toggle_favorite(request, product_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)

    product = get_object_or_404(Product, id=product_id)
    favorite = FavoriteItem.objects.filter(user=request.user, product=product)

    if favorite.exists():
        favorite.delete()
        action = 'removed'
    else:
        FavoriteItem.objects.create(user=request.user, product=product)
        action = 'added'

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

# =====================================================================
# 8. CANCEL ORDER — restores stock
# =====================================================================
@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status not in ['Pending', 'Processing']:
        messages.error(request, "This order cannot be cancelled.")
        return redirect('store:order_history')

    # Restore stock for each item
    for item in order.items.all():
        item.product.stock += item.quantity
        item.product.save()

    order.status = 'Cancelled'
    order.save()

    messages.success(request, f"Order #{order.order_number} cancelled. Stock restored.")
    return redirect('store:order_history')

# =====================================================================
# 9. NEWSLETTER
# =====================================================================
@csrf_protect
def newsletter_subscribe(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip().lower()

            if not email:
                return JsonResponse({'status': 'error', 'message': 'Email address is required.'}, status=400)

            strict_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(strict_pattern, email):
                return JsonResponse({'status': 'error', 'message': 'Please enter a valid email with a standard domain (e.g., @gmail.com).'}, status=200)

            try:
                validate_email(email)
            except ValidationError:
                return JsonResponse({'status': 'error', 'message': 'Invalid email formatting detected.'}, status=200)

            if NewsletterSubscriber.objects.filter(email=email).exists():
                return JsonResponse({'status': 'info', 'message': 'You are already a valued VIP insider!'}, status=200)

            NewsletterSubscriber.objects.create(email=email)
            return JsonResponse({'status': 'success', 'message': 'Welcome to the inner circle! Access granted.'}, status=201)

        except IntegrityError:
            return JsonResponse({'status': 'info', 'message': 'You are already a valued VIP insider!'}, status=200)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': 'An unexpected processing fault occurred.'}, status=200)

    return JsonResponse({'status': 'error', 'message': 'Invalid subscription request method.'}, status=400)


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


    from .models import Review
  

    review, created = Review.objects.update_or_create(
        user=request.user,
        product=product,
        defaults={'rating': rating, 'comment': comment}
    )

    avg = Review.objects.filter(product=product).aggregate(Avg('rating'))['rating__avg']
    product.rating = round(avg, 1)
    product.save()

    total_reviews = Review.objects.filter(product=product).count()

    return JsonResponse({
        'success': True,
        'message': 'Review submitted successfully!',
        'new_rating': float(product.rating),
        'total_reviews': total_reviews,
        'created': created
    })










