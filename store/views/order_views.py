from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import Order
from ..activity_logger import log_action


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


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status not in ['Pending', 'Processing']:
        messages.error(request, "This order cannot be cancelled.")
        return redirect('store:order_history')

    for item in order.items.all():
        item.product.stock += item.quantity
        item.product.save()

    order.status = 'Cancelled'
    order.save()

    log_action(request.user, 'order_cancel', f"Cancelled order #{order.order_number}",
               {'order_id': order.id, 'order_number': order.order_number, 'total': str(order.total_amount)}, request)
    messages.success(request, f"Order #{order.order_number} cancelled. Stock restored.")
    return redirect('store:order_history')
