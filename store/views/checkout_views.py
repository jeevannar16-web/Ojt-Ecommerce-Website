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
        elif not re.match(r'^\+?[\d\s\-\(\)]{7,20}$', phone_number):
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
                'form_data': request.POST
            })

        profile.phone = phone_number
        profile.address_line1 = shipping_address
        profile.city = city
        profile.state = province
        profile.zip_code = postal_code
        profile.save()

        generated_order_number = uuid.uuid4().hex[:10].upper()

        address_parts = [shipping_address, city]
        if province:
            address_parts.append(province)
        if postal_code:
            address_parts.append(f"ZIP: {postal_code}")
        full_shipping_address = ", ".join(address_parts)

        order = Order.objects.create(
            user=request.user,
            order_number=generated_order_number,
            full_name=full_name,
            email=email,
            shipping_address=full_shipping_address,
            total_amount=total_amount,
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
    }
    return render(request, 'store/checkout.html', {
        'cart_items': cart_items,
        'total_amount': total_amount,
        'form_data': form_data,
    })
