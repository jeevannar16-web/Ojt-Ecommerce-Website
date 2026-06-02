from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, CartItem, Order, OrderItem

# =====================================================================
# 1. ADD TO CART VIEW (AUTHENTICATED DATABASE HOOKS)
# =====================================================================
def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Please log in first.'}, status=401)
        
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        
        # Save securely to your real database table
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
    """
    Renders the active shipping cart, extracting authentic items from the database 
    if a user is logged in, or fallback mock sessions if testing.
    """
    cart_items = []
    subtotal = 0.0

    if request.user.is_authenticated:
        # PULL AUTHENTIC USER DATA ITEMS FROM DATABASE
        db_items = CartItem.objects.filter(user=request.user)
        for item in db_items:
            item_total = float(item.product.price) * int(item.quantity)
            subtotal += item_total
            cart_items.append({
                'product': item.product,
                'quantity': item.quantity,
                'total_price': item_total,
                'id': item.id  # Passes the CartItem record ID cleanly
            })
    else:
        # FALLBACK SESSION CONTROLS (If user is browsing anonymously)
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
                    'id': product.id  # 💡 KEEP THIS UNIFORM WITH THE TEMPLATE LOOP!
                })
            except Product.DoesNotExist:
                continue

    # Process promotional coupons
    promo_code = request.GET.get('promo_code', '').strip().upper()
    promo_applied = False
    if promo_code == "FIT-CODEX":
        subtotal *= 0.005  
        promo_applied = True

    context = {
        'cart_items': cart_items,
        'total_amount': round(subtotal, 2),
        'promo_applied': promo_applied,
        'promo_code': promo_code,
    }
    return render(request, 'store/cart.html', context)







def update_cart_quantity(request, product_id, action):
    """
    Increments, decrements, or removes an item from the cart registry database or session.
    """
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
        # SESSION CONTROLS FALLBACK
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
    """
    Pulls authenticated user items, creates a permanent database order, 
    populates sub-items, and cleanly flushes the shopping cart.
    """
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
            
        # Write permanent Order entry log record
        order = Order.objects.create(
            user=request.user,
            full_name=full_name,
            email=email,
            shipping_address=f"{shipping_address}, {city} (ZIP: {postal_code})",
            total_amount=total_amount,
            status='Pending'
        )
        
        # Convert items cleanly to relational lines
        for item in db_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.product.price,
                quantity=item.quantity
            )
            
        # Empty out user cart contents entirely
        db_items.delete()
        
        messages.success(request, f"Thank you! Your fitness order #{order.id} has been placed successfully.")
        return redirect('store:sale_catalog')
        
    return render(request, 'store/checkout.html', {'cart_items': cart_items, 'total_amount': total_amount})


# =====================================================================
# 4. PRODUCT DIRECTORY PAGES & DIRECTORIES
# =====================================================================
def product_list(request):
    products = Product.objects.all()
    recommendations = Product.objects.all().order_by('?')[:4]
    context = {
        'products': products,
        'recommendations': recommendations,
        'title': 'Our Full Catalog'
    }
    return render(request, 'store/product_list.html', context)


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    recommendations = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    if not recommendations.exists():
        recommendations = Product.objects.exclude(id=product.id)[:4]
    context = {
        'product': product,
        'recommendations': recommendations
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