from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import FavoriteItem, Product, CartItem, Order, OrderItem 
import json
from django.views.decorators.csrf import csrf_protect

from django.db import IntegrityError
from .models import NewsletterSubscriber








import re # Import standard regular expressions tool
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

# =====================================================================
# 1. ADD TO CART VIEW (AUTHENTICATED DATABASE HOOKS)
# =====================================================================
def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Please log in first.'}, status=401)
        
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
        if not created:
            cart_item.quantity += 1
            cart_item.save()
            
        return JsonResponse({'success': True, 'message': 'Product added to cart successfully!'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)

# =====================================================================
# 2. CART VIEW & CONTROLS (BALANCED DB + SESSION RECOVERY)
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
        if 'cart' not in request.session:
            request.session['cart'] = {'1': 6, '2': 6}
    
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
    
    # ✅ FIXED: 20% discount logic was multiplying by 0.005 instead of reducing by 20%
    if promo_code == "FIT-CODEX":
        subtotal = float(subtotal) * 0.80  # Correctly applies a 20% discount ($2,850.00 -> $2,280.00)
        promo_applied = True

    context = {
        'cart_items': cart_items,
        'grand_total': round(subtotal, 2),  # Variable matching your updated templates cleanly
        'total_amount': round(subtotal, 2),
        'promo_applied': promo_applied,
        'promo_code': promo_code,
    }
    return render(request, 'store/cart.html', context)


def update_cart_quantity(request, product_id, action):
    if request.user.is_authenticated:
        cart_item = get_object_or_404(CartItem, id=product_id, user=request.user)
        
        if action == 'add':
            cart_item.quantity += 1
            cart_item.save()
        elif action == 'remove':
            cart_item.quantity -= 1
            if cart_item.quantity <= 0:
                cart_item.delete()
            else:
                cart_item.save()
        elif action == 'delete':
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
# 3. SECURE CHECKOUT & ORDER COMPLETION PROCESSING
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
            
        order = Order.objects.create(
            user=request.user,
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
            
        db_items.delete()
        messages.success(request, f"Thank you! Your fitness order #{order.id} has been placed successfully.")
        return redirect('store:sale_catalog')
        
    return render(request, 'store/checkout.html', {'cart_items': cart_items, 'total_amount': total_amount})


# =====================================================================
# 4. PRODUCT DIRECTORY PAGES & DIRECTORIES
# =====================================================================
def product_list(request):
    products = Product.objects.all()
    title = "Our Full Catalog"
    is_search = False
    
    # 1. Capture category parameter safely
    category_id = request.GET.get('category')
    
    if category_id:
        try:
            products = products.filter(category_id=int(category_id))
            if products.exists():
                # Explicitly override title context
                title = f"Elite {products.first().category.name} Collection"
        except (ValueError, TypeError):
            pass

    # 2. Extract true search texts ONLY if user typed inside input field
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
    recommendations = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    if not recommendations.exists():
        recommendations = Product.objects.exclude(id=product.id)[:4]
        
    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = FavoriteItem.objects.filter(user=request.user, product=product).exists()
        
    context = {
        'product': product,
        'recommendations': recommendations,
        'is_favorited': is_favorited  
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
# 5. WISHLIST / FAVORITES PROCESSING LOGIC
# =====================================================================
def toggle_favorite(request, product_id):
    """Asynchronously adds or removes an item from favorites"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Please log in first.'}, status=401)
        
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        favorite_exists = FavoriteItem.objects.filter(user=request.user, product=product).exists()
        
        # Recalculate remaining total count for accurate navigation header synchronization
        if favorite_exists:
            FavoriteItem.objects.filter(user=request.user, product=product).delete()
            total_favorites = FavoriteItem.objects.filter(request.user).count()
            return JsonResponse({'success': True, 'action': 'removed', 'total_favorites': total_favorites, 'message': 'Removed from favorites!'})
        else:
            FavoriteItem.objects.create(user=request.user, product=product)
            total_favorites = FavoriteItem.objects.filter(user=request.user).count()
            return JsonResponse({'success': True, 'action': 'added', 'total_favorites': total_favorites, 'message': 'Added to favorites!'})
            
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)


@login_required(login_url='/users/login/')
def favorites_list(request):
    # Handle AJAX DELETE requests safely
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            
            # Using FavoriteItem to match your standard model creation paths
            favorite_item = FavoriteItem.objects.filter(user=request.user, product_id=product_id)
            if favorite_item.exists():
                favorite_item.delete()
                
            total_favorites = FavoriteItem.objects.filter(user=request.user).count()
            return JsonResponse({'status': 'deleted', 'total_favorites': total_favorites})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
            
    # Standard page display logic path
    favorite_items = FavoriteItem.objects.filter(user=request.user)
    return render(request, 'store/favorites.html', {'favorite_items': favorite_items})









@csrf_protect
def newsletter_subscribe(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip().lower()
            
            if not email:
                return JsonResponse({'status': 'error', 'message': 'Email address is required.'}, status=400)
            
            # 1. Strict pattern check ensuring a real domain suffix exists (e.g., .com)
            strict_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(strict_pattern, email):
                return JsonResponse({'status': 'error', 'message': 'Please enter a valid email with a standard domain (e.g., @gmail.com).'}, status=200)

            # 2. Django system-level structural check
            try:
                validate_email(email)
            except ValidationError:
                return JsonResponse({'status': 'error', 'message': 'Invalid email formatting detected.'}, status=200)
                
            # 3. Handle duplicates gracefully
            if NewsletterSubscriber.objects.filter(email=email).exists():
                return JsonResponse({'status': 'info', 'message': 'You are already a valued VIP insider!'}, status=200)
                
            # 4. Save clean data record row entry
            NewsletterSubscriber.objects.create(email=email)
            return JsonResponse({'status': 'success', 'message': 'Welcome to the inner circle! Access granted.'}, status=201)
            
        except IntegrityError:
            return JsonResponse({'status': 'info', 'message': 'You are already a valued VIP insider!'}, status=200)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': 'An unexpected processing fault occurred.'}, status=200)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid subscription request method.'}, status=400)