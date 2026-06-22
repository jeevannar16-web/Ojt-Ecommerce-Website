from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
import json
from ..models import CartItem, Product, ProductSize
from ..activity_logger import log_action


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

    return JsonResponse({
        'success': True,
        'message': f'{product.name} added to your bag!',
        'cart_count': total_cart_items,
    })


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
                'id': item.id,
                'size': item.size or None,
            })
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


def update_cart_quantity(request, product_id, action):
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

    return redirect('store:cart')
