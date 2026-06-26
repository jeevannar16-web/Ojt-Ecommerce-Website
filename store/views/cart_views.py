"""Cart operations — add, remove, update quantities, clear, and coupon validation."""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
import json
from datetime import datetime, timedelta
from ..models import CartItem, Product, ProductSize, Category
from ..activity_logger import log_action


# ==============================================================================
# SECTION: Add to Cart
# ==============================================================================

def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'requires_login': True,
            'message': 'Please sign in to add items to your bag.'
        }, status=401)

    product = get_object_or_404(Product, id=product_id)
    qty = 1
    size_name = None

    if request.body:
        try:
            body = json.loads(request.body)
            qty = int(body.get('quantity', 1))
            size_name = body.get('size', None)
        except (ValueError, TypeError, json.JSONDecodeError):
            qty = 1

    if qty < 1:
        qty = 1

    if product.has_sizes:
        if not size_name:
            return JsonResponse({
                'success': False,
                'message': 'Please select a size.'
            })
        try:
            ps = ProductSize.objects.get(product=product, size=size_name)
        except ProductSize.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': f'Size "{size_name}" is not available for this product.'
            })
        if ps.stock < qty:
            return JsonResponse({
                'success': False,
                'message': f'Only {ps.stock} unit{"s" if ps.stock != 1 else ""} available in size {size_name}!'
            })
        ps.stock -= qty
        ps.save()
    else:
        if product.stock < qty:
            return JsonResponse({
                'success': False,
                'message': f'Only {product.stock} unit{"s" if product.stock != 1 else ""} available!'
            })
        product.stock -= qty
        product.save()

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
        size=size_name or '',
        defaults={'quantity': qty}
    )

    if not created:
        cart_item.quantity += qty
        cart_item.save()

    log_action(request.user, 'cart_add', f"Added {qty}x {product.name}{' ('+size_name+')' if size_name else ''} to cart",
               {'product_id': product.id, 'product_name': product.name, 'quantity': qty, 'size': size_name}, request)

    total_cart_items = CartItem.objects.filter(
        user=request.user
    ).aggregate(total=Sum('quantity'))['total'] or 0

    response_data = {
        'success': True,
        'message': f'{product.name} added to your bag!',
        'cart_count': total_cart_items,
    }

    if product.has_sizes:
        sizes_qs = ProductSize.objects.filter(product=product)
        response_data['has_sizes'] = True
        response_data['sizes'] = [{'size': ps.size, 'stock': ps.stock} for ps in sizes_qs]
    else:
        response_data['has_sizes'] = False
        response_data['stock_remaining'] = product.stock

    return JsonResponse(response_data)


# ==============================================================================
# SECTION: Cart View
# ==============================================================================

def cart_view(request):
    cart_items = []
    subtotal = 0.0

    filters = {}
    if request.user.is_authenticated:
        db_items = CartItem.objects.filter(user=request.user)

        cat = request.GET.get('category', '').strip()
        if cat:
            db_items = db_items.filter(product__category__name__iexact=cat)

        seller = request.GET.get('seller', '').strip()
        if seller:
            db_items = db_items.filter(product__seller__username__iexact=seller)

        price_min = request.GET.get('price_min', '').strip()
        if price_min:
            try:
                db_items = db_items.filter(product__price__gte=float(price_min))
            except ValueError:
                pass

        price_max = request.GET.get('price_max', '').strip()
        if price_max:
            try:
                db_items = db_items.filter(product__price__lte=float(price_max))
            except ValueError:
                pass

        date_from = request.GET.get('date_from', '').strip()
        if date_from:
            try:
                dt = datetime.strptime(date_from, '%Y-%m-%d')
                db_items = db_items.filter(added_at__gte=dt)
            except ValueError:
                pass

        date_to = request.GET.get('date_to', '').strip()
        if date_to:
            try:
                dt = datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
                db_items = db_items.filter(added_at__lte=dt)
            except ValueError:
                pass

        sort = request.GET.get('sort', '').strip()
        if sort == 'price_asc':
            db_items = db_items.order_by('product__price')
        elif sort == 'price_desc':
            db_items = db_items.order_by('-product__price')
        elif sort == 'newest':
            db_items = db_items.order_by('-added_at')
        elif sort == 'oldest':
            db_items = db_items.order_by('added_at')
        elif sort == 'name_asc':
            db_items = db_items.order_by('product__name')
        elif sort == 'qty_desc':
            db_items = db_items.order_by('-quantity')
        else:
            db_items = db_items.order_by('-added_at')

        for item in db_items:
            item_total = float(item.product.price) * int(item.quantity)
            subtotal += item_total
            cart_items.append({
                'product': item.product,
                'quantity': item.quantity,
                'total_price': item_total,
                'id': item.id,
                'size': item.size or None,
                'added_at': item.added_at,
            })

        cats_in_cart = Category.objects.filter(
            products__cartitem__user=request.user
        ).distinct()
        sellers_in_cart = Product.objects.filter(
            cartitem__user=request.user
        ).values_list('seller__username', flat=True).distinct()
        filters = {
            'categories': cats_in_cart,
            'sellers': sellers_in_cart,
            'current_category': request.GET.get('category', ''),
            'current_seller': request.GET.get('seller', ''),
            'current_price_min': request.GET.get('price_min', ''),
            'current_price_max': request.GET.get('price_max', ''),
            'current_date_from': request.GET.get('date_from', ''),
            'current_date_to': request.GET.get('date_to', ''),
            'current_sort': request.GET.get('sort', ''),
        }
    else:
        session_cart = request.session.get('cart', {})
        for product_id, data in session_cart.items():
            try:
                product = Product.objects.get(id=int(product_id))
                qty = data['qty'] if isinstance(data, dict) else data
                sz = data.get('size') if isinstance(data, dict) else None
                item_total = float(product.price) * int(qty)
                subtotal += item_total
                cart_items.append({
                    'product': product,
                    'quantity': qty,
                    'total_price': item_total,
                    'id': product.id,
                    'size': sz,
                    'added_at': None,
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
        'filters': filters,
    }
    return render(request, 'store/cart.html', context)


# ==============================================================================
# SECTION: Update Cart Quantity
# ==============================================================================

def update_cart_quantity(request, product_id, action):
    is_ajax = request.GET.get('_ajax') == '1'
    if request.user.is_authenticated:
        cart_item = get_object_or_404(CartItem, id=product_id, user=request.user)
        product = cart_item.product

        if cart_item.size:
            ps = ProductSize.objects.filter(product=product, size=cart_item.size).first()
        else:
            ps = None

        if action == 'add':
            if ps:
                if ps.stock > 0:
                    cart_item.quantity += 1
                    cart_item.save()
                    ps.stock -= 1
                    ps.save()
            else:
                if product.stock > 0:
                    cart_item.quantity += 1
                    cart_item.save()
                    product.stock -= 1
                    product.save()
            log_action(request.user, 'cart_update', f"Increased {product.name} qty to {cart_item.quantity}",
                       {'product_id': product.id, 'product_name': product.name, 'quantity': cart_item.quantity, 'action': 'increase'}, request)
        elif action == 'remove':
            cart_item.quantity -= 1
            if ps:
                ps.stock += 1
                ps.save()
            else:
                product.stock += 1
                product.save()
            if cart_item.quantity <= 0:
                log_action(request.user, 'cart_remove', f"Removed {product.name} from cart",
                           {'product_id': product.id, 'product_name': product.name, 'action': 'remove'}, request)
                cart_item.delete()
            else:
                cart_item.save()
                log_action(request.user, 'cart_update', f"Decreased {product.name} qty to {cart_item.quantity}",
                           {'product_id': product.id, 'product_name': product.name, 'quantity': cart_item.quantity, 'action': 'decrease'}, request)
        elif action == 'delete':
            qty_removed = cart_item.quantity
            if ps:
                ps.stock += cart_item.quantity
                ps.save()
            else:
                product.stock += cart_item.quantity
                product.save()
            log_action(request.user, 'cart_remove', f"Removed {qty_removed}x {product.name} from cart",
                       {'product_id': product.id, 'product_name': product.name, 'quantity': qty_removed, 'action': 'delete'}, request)
            cart_item.delete()
    else:
        cart = request.session.get('cart', {})
        str_id = str(product_id)
        if str_id in cart:
            if isinstance(cart[str_id], dict):
                qty = cart[str_id]['qty']
            else:
                qty = cart[str_id]
            if action == 'add':
                qty += 1
            elif action == 'remove':
                qty -= 1
                if qty <= 0:
                    del cart[str_id]
                else:
                    if isinstance(cart.get(str_id), dict):
                        cart[str_id]['qty'] = qty
                    else:
                        cart[str_id] = qty
            elif action == 'delete':
                del cart[str_id]
            else:
                if isinstance(cart.get(str_id), dict):
                    cart[str_id]['qty'] = qty
                else:
                    cart[str_id] = qty
        request.session['cart'] = cart
        request.session.modified = True

    if is_ajax:
        from django.db.models import Sum
        total_cart_qty = CartItem.objects.filter(user=request.user).aggregate(total=Sum('quantity'))['total'] or 0
        return JsonResponse({
            'success': True,
            'action': action,
            'cart_count': total_cart_qty,
        })
    return redirect('store:cart')


# ==============================================================================
# SECTION: Batch Delete
# ==============================================================================

@login_required
def cart_batch_delete(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
    except (ValueError, TypeError):
        data = request.POST

    item_ids = data.get('item_ids', [])
    if not item_ids:
        return JsonResponse({'success': False, 'error': 'No items specified'})

    if isinstance(item_ids, str):
        try:
            item_ids = json.loads(item_ids)
        except (ValueError, TypeError):
            item_ids = [int(x) for x in item_ids.split(',') if x.strip().isdigit()]

    deleted_count = 0
    for item_id in item_ids:
        try:
            cart_item = CartItem.objects.get(id=item_id, user=request.user)
            product = cart_item.product
            qty = cart_item.quantity
            if cart_item.size:
                ps = ProductSize.objects.filter(product=product, size=cart_item.size).first()
                if ps:
                    ps.stock += qty
                    ps.save()
                else:
                    product.stock += qty
                    product.save()
            else:
                product.stock += qty
                product.save()
            log_action(request.user, 'cart_remove', f"Removed {qty}x {product.name} from cart (batch)",
                       {'product_id': product.id, 'product_name': product.name, 'quantity': qty, 'action': 'batch_delete'}, request)
            cart_item.delete()
            deleted_count += 1
        except CartItem.DoesNotExist:
            pass

    from django.db.models import Sum
    total_cart_qty = CartItem.objects.filter(user=request.user).aggregate(total=Sum('quantity'))['total'] or 0
    return JsonResponse({
        'success': True,
        'deleted_count': deleted_count,
        'cart_count': total_cart_qty,
    })


# ==============================================================================
# SECTION: Cart Mini API
# ==============================================================================

@login_required
def cart_mini_api(request):
    items = CartItem.objects.filter(user=request.user).select_related('product')
    cart_data = []
    total = 0
    for ci in items:
        subtotal = ci.product.price * ci.quantity
        total += subtotal
        cart_data.append({
            'id': ci.id,
            'product_id': ci.product.id,
            'name': ci.product.name,
            'price': float(ci.product.price),
            'quantity': ci.quantity,
            'subtotal': float(subtotal),
            'image': ci.product.image.url if ci.product.image else '',
            'size': ci.size or '',
        })
    from django.db.models import Sum as SumAgg
    cart_qty = CartItem.objects.filter(user=request.user).aggregate(total=SumAgg('quantity'))['total'] or 0
    return JsonResponse({
        'success': True,
        'items': cart_data,
        'total': float(total),
        'cart_count': cart_qty,
    })
