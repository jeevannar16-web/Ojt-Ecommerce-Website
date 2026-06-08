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

from django.db.models import Count

import os

import base64
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile



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
            cat = Category.objects.filter(id=int(category_id)).first()
            if cat:
                title = f"Elite {cat.name} Collection"
        except (ValueError, TypeError):
            pass

    search_query = request.GET.get('search', '').strip()
    if search_query:
        products = products.filter(name__icontains=search_query)
        title = f'Search Results for "{search_query}"'
        is_search = True

    price_min = request.GET.get('price_min', '').strip()
    price_max = request.GET.get('price_max', '').strip()
    if price_min:
        try:
            products = products.filter(price__gte=float(price_min))
        except ValueError:
            pass
    if price_max:
        try:
            products = products.filter(price__lte=float(price_max))
        except ValueError:
            pass

    selected_types = request.GET.getlist('type')
    if selected_types:
        products = products.filter(category__name__in=selected_types)

    only_available = request.GET.get('available') == '1'
    if only_available:
        products = products.filter(stock__gt=0)

    goal = request.GET.get('goal', '').strip()
    GOAL_MAP = {
        'muscle': ['Dumbbells', 'Barbells', 'Weight Plates', 'Kettlebells'],
        'home':   ['Resistance Bands', 'Pull-Up Bars', 'Yoga Mats'],
        'loss':   ['Cardio', 'Resistance Bands', 'Jump Ropes'],
        'cardio': ['Cardio', 'Treadmills', 'Rowing Machines'],
    }
    if goal and goal in GOAL_MAP:
        products = products.filter(category__name__in=GOAL_MAP[goal])

    # ── Sorting ──
    sort = request.GET.get('sort', '')
    SORT_MAP = {
        'price_asc':   'price',
        'price_desc':  '-price',
        'rating_desc': '-rating',
        'name_asc':    'name',
        'newest':      '-id',
    }
    if sort in SORT_MAP:
        products = products.order_by(SORT_MAP[sort])

    all_categories = Category.objects.filter(products__isnull=False).distinct()
    recommendations = Product.objects.all().order_by('?')[:4]

    context = {
        'products': products,
        'recommendations': recommendations,
        'title': title,
        'is_search': is_search,
        'all_categories': all_categories,
        'selected_types': selected_types,
        'price_min': price_min,
        'price_max': price_max,
        'only_available': only_available,
        'active_goal': goal,
        'active_category_id': category_id or '',
        'active_sort': sort,
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

    # Calculate rating breakdown efficiently
    # Group by rating and count them in a single query
    rating_counts = reviews.values('rating').annotate(count=Count('id'))
    counts_dict = {item['rating']: item['count'] for item in rating_counts}

    rating_breakdown = {}
    for i in range(1, 6):
        count = counts_dict.get(i, 0)
        percentage = round((count / total_reviews) * 100) if total_reviews > 0 else 0
        rating_breakdown[i] = {
            'count': count,
            'percentage': percentage
        }

    # --- FIX FOR THE TEMPLATE ERROR ---
    # Convert comma-separated string to a list, stripping any accidental whitespace
    if product.size:
        size_list = [sz.strip() for sz in product.size.split(',') if sz.strip()]
    else:
        size_list = []

    context = {
        'product': product,
        'recommendations': recommendations,
        'is_favorited': is_favorited,
        'reviews': reviews,
        'total_reviews': total_reviews,
        'user_review': user_review,
        'has_purchased': has_purchased,
        'rating_breakdown': rating_breakdown,
        'size_list': size_list,  # Added to context
    }
    return render(request, 'store/product_detail.html', context)
def sale_catalog(request):
    # Fetch existing filter/sort items if they exist in GET parameters
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    active_sort = request.GET.get('sort', '')

    # ... Your existing query filters logic goes here ...
    products = Product.objects.filter(is_sale=True)
    recommendations = Product.objects.filter(is_featured=True)[:4]

    context = {
        'products': products,
        'recommendations': recommendations,
        'title': 'Flash Sale Collection',
        'is_sale_page': True,
        
        # ADD THESE TO YOUR CONTEXT BLOCK:
        'price_min': price_min,
        'price_max': price_max,
        'active_sort': active_sort,
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



# 1. Main Curation Board View
def curation_workspace(request):
    products = Product.objects.all().order_by('id')
    return render(request, 'store/curation.html', {'products': products})


# Helper Function: Automatically rewrites the store.json file with updated paths
def sync_database_to_json_fixture():
    fixtures = []
    
    # Export categories first to satisfy database foreign keys constraint order
    for cat in Category.objects.all():
        cat_img = str(cat.image) if cat.image else ""
        fixtures.append({
            "model": "store.category",
            "pk": cat.id,
            "fields": {
                "name": cat.name,
                "image": cat_img
            }
        })
        
    # Export products downstream with current updates
    for prod in Product.objects.all():
        prod_img = str(prod.image) if prod.image else ""
        fixtures.append({
            "model": "store.product",
            "pk": prod.id,
            "fields": {
                "category": prod.category.id if prod.category else None,
                "name": prod.name,
                "price": str(prod.price),
                "stock": prod.stock,
                "description": prod.description,
                "image": prod_img,
                "is_featured": prod.is_featured,
                "is_sale": prod.is_sale,
                "rating": str(prod.rating),
                "size": prod.size
            }
        })
        
    # Overwrites your store.json file on your disk path
    fixture_path = os.path.join(settings.BASE_DIR, 'store.json')
    with open(fixture_path, 'w') as f:
        json.dump(fixtures, f, indent=2)


# 2. Universal API Endpoint: Handles saving to products/ or category_images/ folders
@csrf_exempt
def update_curation_asset(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product = Product.objects.get(id=data.get('id'))
            image_data = data.get('image')
            target_type = data.get('target_type', 'product')  # 'product' or 'category'

            if not image_data.startswith('data:image'):
                return JsonResponse({'status': 'error', 'message': 'Invalid image data format'}, status=400)

            # Decode browser base64 clipboard data stream
            format, imgstr = image_data.split(';base64,')
            ext = format.split('/')[-1]
            raw_binary_file = ContentFile(base64.b64decode(imgstr))

            if target_type == 'category':
                if not product.category:
                    return JsonResponse({'status': 'error', 'message': 'This product has no assigned category'}, status=400)
                
                category = product.category
                file_name = f"curated_cat_{category.id}.{ext}"
                
                # Natively triggers category ImageField upload_to='category_images/'
                category.image.save(file_name, raw_binary_file, save=True)
                message = "Successfully saved to category_images/ and synced store.json!"
            
            else:
                file_name = f"curated_prod_{product.id}.{ext}"
                
                # Natively triggers product ImageField upload_to='products/'
                product.image.save(file_name, raw_binary_file, save=True)
                message = "Successfully saved to products/ and synced store.json!"

            # Instantly mirror current updates back out to store.json file on disk
            sync_database_to_json_fixture()

            return JsonResponse({'status': 'success', 'message': message})
            
        except Product.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Product missing'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)