"""Checkout flow — delivery address, shipping selection, payment, and order placement with map picking."""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import re
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from ..models import CartItem, Order, OrderItem
from ..activity_logger import log_action
from users.models import Profile
import uuid


# ==============================================================================
# SECTION: Checkout View
# ==============================================================================

@login_required
def checkout_view(request):
    items_param = request.GET.get('items', '').strip()
    if items_param:
        try:
            selected_ids = [int(x) for x in items_param.split(',') if x.strip().isdigit()]
            db_items = CartItem.objects.filter(user=request.user, id__in=selected_ids)
        except (ValueError, TypeError):
            db_items = CartItem.objects.filter(user=request.user)
    else:
        db_items = CartItem.objects.filter(user=request.user)

    if not db_items.exists():
        messages.error(request, "No items selected for checkout.")
        return redirect('store:cart')

    cart_items = []
    total_amount = 0.0
    for item in db_items:
        item_total = float(item.product.price) * int(item.quantity)
        total_amount += item_total
        cart_items.append({
            'product': item.product,
            'quantity': item.quantity,
            'total_price': item_total,
            'size': item.size or None,
        })

    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        shipping_address = request.POST.get('shipping_address', '').strip()
        city = request.POST.get('city', '').strip()
        province = request.POST.get('province', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()
        latitude = request.POST.get('latitude', '').strip()
        longitude = request.POST.get('longitude', '').strip()
        coupon_code = request.POST.get('coupon_code', '').strip().upper()

        discount_amount = 0.0
        final_amount = total_amount
        coupon_valid = False
        if coupon_code == "FIT-CODEX":
            if total_amount >= 7.0:
                discount_amount = round(total_amount * 0.20, 2)
                final_amount = round(total_amount - discount_amount, 2)
                coupon_valid = True

        # If "Apply" coupon button was clicked, re-render without creating order
        if request.POST.get('apply_coupon'):
            return render(request, 'store/checkout.html', {
                'cart_items': cart_items,
                'total_amount': total_amount,
                'final_amount': final_amount,
                'form_data': request.POST,
                'coupon_code': coupon_code,
                'discount_amount': discount_amount,
                'coupon_valid': coupon_valid,
            })

        errors = []
        if not full_name:
            errors.append("Full name is required.")
        if not email:
            errors.append("Email address is required.")
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors.append("Please enter a valid email address.")
        if not phone_number:
            errors.append("Phone number is required.")
        elif not re.match(r'^\+?[\d\s\-\(\)]{7,20}$', phone_number) or len(re.sub(r'[\s\-\(\)\+]', '', phone_number)) < 7:
            errors.append("Please enter a valid phone number (e.g. +92 300 1234567).")
        if not shipping_address:
            errors.append("Street address is required.")
        if not city:
            errors.append("City is required.")
        if not province:
            errors.append("Province/State is required.")

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, 'store/checkout.html', {
                'cart_items': cart_items,
                'total_amount': total_amount,
                'final_amount': final_amount,
                'form_data': request.POST,
                'coupon_code': coupon_code,
                'discount_amount': discount_amount,
                'coupon_valid': coupon_valid,
            })

        profile.phone = phone_number
        profile.address_line1 = shipping_address
        profile.city = city
        profile.state = province
        profile.zip_code = postal_code
        if latitude:
            try:
                profile.latitude = float(latitude)
            except (ValueError, TypeError):
                pass
        if longitude:
            try:
                profile.longitude = float(longitude)
            except (ValueError, TypeError):
                pass
        profile.save()

        generated_order_number = uuid.uuid4().hex[:10].upper()

        address_parts = [shipping_address, city]
        if province:
            address_parts.append(province)
        if postal_code:
            address_parts.append(f"ZIP: {postal_code}")
        full_shipping_address = ", ".join(address_parts)

        order_lat = None
        order_lng = None
        if latitude:
            try:
                order_lat = float(latitude)
            except (ValueError, TypeError):
                pass
        if longitude:
            try:
                order_lng = float(longitude)
            except (ValueError, TypeError):
                pass

        order = Order.objects.create(
            user=request.user,
            order_number=generated_order_number,
            full_name=full_name,
            email=email,
            shipping_address=full_shipping_address,
            latitude=order_lat,
            longitude=order_lng,
            total_amount=final_amount,
            coupon_code=coupon_code or None,
            discount_amount=discount_amount,
            status='Pending'
        )

        order_items_list = []
        for item in db_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                size=item.size or None,
                price=item.product.price,
                quantity=item.quantity
            )
            order_items_list.append({
                'product': item.product.name,
                'quantity': item.quantity,
                'size': item.size,
            })

        db_items.delete()
        log_action(request.user, 'order_place', f"Placed order #{order.order_number} (${order.total_amount})",
                   {'order_id': order.id, 'order_number': order.order_number, 'total': str(order.total_amount),
                    'items': order_items_list, 'status': 'Pending'}, request)
        messages.success(request, f"Thank you! Your order #{order.id} has been placed successfully.")
        return redirect('store:order_history')

    form_data = {
        'full_name': request.user.get_full_name(),
        'email': request.user.email,
        'phone_number': profile.phone,
        'shipping_address': profile.address_line1,
        'city': profile.city,
        'province': profile.state,
        'postal_code': profile.zip_code,
        'latitude': profile.latitude or '',
        'longitude': profile.longitude or '',
        'country': profile.country,
    }
    return render(request, 'store/checkout.html', {
        'cart_items': cart_items,
        'total_amount': total_amount,
        'final_amount': total_amount,
        'coupon_code': '',
        'discount_amount': 0,
        'coupon_valid': False,
        'form_data': form_data,
    })
