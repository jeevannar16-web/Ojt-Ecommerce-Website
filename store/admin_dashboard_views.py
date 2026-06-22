from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.contrib.auth.models import User
from .models import Product, Order, OrderItem, Category, Review, NewsletterSubscriber, FavoriteItem, CartItem, ActivityLog
from users.models import Profile
from .activity_logger import log_action
from django.utils.html import escape
from django.core.paginator import Paginator


@staff_member_required
def admin_dashboard(request):
    total_users = User.objects.count()
    total_verified_users = Profile.objects.filter(is_email_verified=True).count()
    total_unverified_users = total_users - total_verified_users
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_revenue = Order.objects.exclude(status='Cancelled').aggregate(t=Sum('total_amount'))['t'] or 0
    total_categories = Category.objects.count()
    total_reviews = Review.objects.count()
    total_subscribers = NewsletterSubscriber.objects.count()

    recent_orders = Order.objects.all().order_by('-created_at')[:10]
    low_stock_products = Product.objects.filter(stock__lt=5).order_by('stock')[:10]

    pending_sellers = Profile.objects.filter(seller_requested=True, is_seller=False).select_related('user')
    current_sellers = Profile.objects.filter(is_seller=True).select_related('user')

    order_status_counts = Order.objects.values('status').annotate(count=Count('id')).order_by('status')
    status_labels = dict(Order.STATUS_CHOICES)
    order_status_breakdown = {item['status']: {'count': item['count'], 'label': status_labels.get(item['status'], item['status'])} for item in order_status_counts}

    total_favorites_count = FavoriteItem.objects.count()
    total_cart_items_count = CartItem.objects.count()
    active_cart_users = CartItem.objects.values('user').distinct().count()

    recent_favorites = FavoriteItem.objects.select_related('user', 'product').order_by('-created_at')[:10]
    recent_cart_items = CartItem.objects.select_related('user', 'product').order_by('-added_at')[:10]
    recent_users = User.objects.all().select_related('profile').order_by('-date_joined')[:10]

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_order_status':
            order_id = request.POST.get('order_id')
            new_status = request.POST.get('status')
            order = get_object_or_404(Order, id=order_id)
            old_status = order.status
            order.status = new_status
            order.save()
            log_action(request.user, 'order_status', f"Order #{order.order_number} status: {old_status} → {new_status}",
                       {'order_id': order.id, 'order_number': order.order_number, 'old_status': old_status, 'new_status': new_status}, request)
            messages.success(request, f"Order #{order.order_number or order.id} updated to '{new_status}'")
        elif action == 'approve_seller':
            user_id = request.POST.get('user_id')
            profile = get_object_or_404(Profile, user_id=user_id)
            profile.is_seller = True
            profile.seller_rejection_reason = ''
            profile.save()
            log_action(request.user, 'seller_approve', f"Approved @{profile.user.username} as seller",
                       {'user_id': profile.user.id, 'username': profile.user.username,
                        'store_name': profile.store_name, 'business_type': profile.business_type}, request)
            messages.success(request, f"@{profile.user.username} is now a seller!")
        elif action == 'decline_seller':
            user_id = request.POST.get('user_id')
            reason = request.POST.get('rejection_reason', '').strip()
            profile = get_object_or_404(Profile, user_id=user_id)
            profile.seller_requested = False
            profile.seller_rejection_reason = reason
            from django.utils import timezone
            profile.seller_requested_at = None
            profile.save()
            log_action(request.user, 'seller_decline', f"Declined @{profile.user.username}'s seller request: {reason}",
                       {'user_id': profile.user.id, 'username': profile.user.username, 'reason': reason}, request)
            messages.success(request, f"@{profile.user.username}'s seller request declined.")
        elif action == 'revoke_seller':
            user_id = request.POST.get('user_id')
            profile = get_object_or_404(Profile, user_id=user_id)
            profile.is_seller = False
            profile.seller_requested = False
            from django.utils import timezone
            profile.seller_requested_at = None
            profile.save()
            log_action(request.user, 'seller_revoke', f"Revoked seller access for @{profile.user.username}",
                       {'user_id': profile.user.id, 'username': profile.user.username}, request)
            messages.success(request, f"@{profile.user.username}'s seller access revoked.")
        return redirect('store:admin_dashboard')

    context = {
        'total_users': total_users,
        'total_verified_users': total_verified_users,
        'total_unverified_users': total_unverified_users,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_categories': total_categories,
        'total_reviews': total_reviews,
        'total_subscribers': total_subscribers,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
        'pending_sellers': pending_sellers,
        'current_sellers': current_sellers,
        'total_favorites_count': total_favorites_count,
        'total_cart_items_count': total_cart_items_count,
        'active_cart_users': active_cart_users,
        'recent_favorites': recent_favorites,
        'recent_cart_items': recent_cart_items,
        'recent_users': recent_users,
        'order_status_breakdown': order_status_breakdown,
    }
    return render(request, 'store/admin_dashboard.html', context)


@staff_member_required
def admin_activity_log(request):
    logs = ActivityLog.objects.all().select_related('user')

    action_filter = request.GET.get('action', '')
    user_filter = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if action_filter:
        logs = logs.filter(action_type=action_filter)
    if user_filter:
        logs = logs.filter(user__username__icontains=user_filter)
    if date_from:
        logs = logs.filter(created_at__gte=date_from)
    if date_to:
        logs = logs.filter(created_at__lte=date_to)

    paginator = Paginator(logs, 50)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)

    action_types = ActivityLog.ACTION_TYPES

    action_counts = {
        item['action_type']: item['count']
        for item in ActivityLog.objects.values('action_type').annotate(count=Count('id'))
    }

    context = {
        'logs': page_obj,
        'page_obj': page_obj,
        'action_types': action_types,
        'action_counts': action_counts,
        'current_action': action_filter,
        'current_user': user_filter,
        'current_date_from': date_from,
        'current_date_to': date_to,
    }
    return render(request, 'store/admin_activity_log.html', context)


@staff_member_required
def admin_favorites(request):
    favorites = FavoriteItem.objects.select_related('user', 'product').order_by('-created_at')

    user_filter = request.GET.get('user', '')
    product_filter = request.GET.get('product', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if user_filter:
        favorites = favorites.filter(user__username__icontains=user_filter)
    if product_filter:
        favorites = favorites.filter(product__name__icontains=product_filter)
    if date_from:
        favorites = favorites.filter(created_at__gte=date_from)
    if date_to:
        favorites = favorites.filter(created_at__lte=date_to)

    total_favs = favorites.count()

    paginator = Paginator(favorites, 50)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)

    top_favorited = FavoriteItem.objects.values('product__name', 'product_id').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    context = {
        'favorites': page_obj,
        'page_obj': page_obj,
        'total_favs': total_favs,
        'top_favorited': top_favorited,
        'current_user': user_filter,
        'current_product': product_filter,
        'current_date_from': date_from,
        'current_date_to': date_to,
    }
    return render(request, 'store/admin_favorites.html', context)


@staff_member_required
def admin_cart(request):
    cart_items = CartItem.objects.select_related('user', 'product').order_by('-added_at')

    user_filter = request.GET.get('user', '')
    product_filter = request.GET.get('product', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if user_filter:
        cart_items = cart_items.filter(user__username__icontains=user_filter)
    if product_filter:
        cart_items = cart_items.filter(product__name__icontains=product_filter)
    if date_from:
        cart_items = cart_items.filter(added_at__gte=date_from)
    if date_to:
        cart_items = cart_items.filter(added_at__lte=date_to)

    total_cart_items_count = cart_items.count()
    total_cart_users = cart_items.values('user').distinct().count()

    paginator = Paginator(cart_items, 50)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)

    top_carted = CartItem.objects.values('product__name', 'product_id').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    total_qty = cart_items.aggregate(t=Sum('quantity'))['t'] or 0

    context = {
        'cart_items': page_obj,
        'page_obj': page_obj,
        'total_cart_items': total_cart_items_count,
        'total_cart_users': total_cart_users,
        'total_qty': total_qty,
        'top_carted': top_carted,
        'current_user': user_filter,
        'current_product': product_filter,
        'current_date_from': date_from,
        'current_date_to': date_to,
    }
    return render(request, 'store/admin_cart.html', context)
