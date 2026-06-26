# ==============================================================================
# Module: store.admin_dashboard_views
# Description: Admin dashboard views
# ==============================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Product, Order, OrderItem, Category, Review, NewsletterSubscriber, FavoriteItem, CartItem, ActivityLog
from users.models import Profile
from .activity_logger import log_action
from django.utils.html import escape
from django.core.paginator import Paginator
from django.db.models.functions import TruncMonth


# ==============================================================================
# SECTION: Admin Dashboard
# ==============================================================================

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


# ==============================================================================
# SECTION: Admin Activity Log
# ==============================================================================

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


# ==============================================================================
# SECTION: Admin Favorites
# ==============================================================================

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


# ==============================================================================
# SECTION: Admin Cart
# ==============================================================================

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


# ==============================================================================
# SECTION: Admin Sellers
# ==============================================================================

@staff_member_required
def admin_sellers(request):
    search = request.GET.get('search', '').strip()
    sort = request.GET.get('sort', 'name')
    verified_filter = request.GET.get('verified', '')

    sellers = Profile.objects.filter(is_seller=True).select_related('user')

    if search:
        sellers = sellers.filter(Q(user__username__icontains=search) | Q(store_name__icontains=search) | Q(user__email__icontains=search))
    if verified_filter == 'yes':
        sellers = sellers.filter(is_email_verified=True)
    elif verified_filter == 'no':
        sellers = sellers.filter(is_email_verified=False)

    seller_data = []
    for p in sellers:
        products = Product.objects.filter(seller=p.user)
        prod_count = products.count()
        order_items = OrderItem.objects.filter(product__in=products.values('id'))
        total_rev = order_items.aggregate(t=Sum('price'))['t'] or 0
        total_units = order_items.aggregate(t=Sum('quantity'))['t'] or 0
        total_orders = order_items.values('order').distinct().count()
        low_stock_count = products.filter(stock__gt=0, stock__lt=5).count()
        out_of_stock_count = products.filter(stock=0).count()

        seller_data.append({
            'profile': p,
            'user': p.user,
            'product_count': prod_count,
            'total_revenue': total_rev,
            'total_units_sold': total_units,
            'total_orders': total_orders,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
        })

    if sort == 'revenue':
        seller_data.sort(key=lambda x: x['total_revenue'], reverse=True)
    elif sort == 'orders':
        seller_data.sort(key=lambda x: x['total_orders'], reverse=True)
    elif sort == 'products':
        seller_data.sort(key=lambda x: x['product_count'], reverse=True)
    elif sort == 'units':
        seller_data.sort(key=lambda x: x['total_units_sold'], reverse=True)
    else:
        seller_data.sort(key=lambda x: x['user'].username.lower())

    paginator = Paginator(seller_data, 20)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)

    total_sellers = Profile.objects.filter(is_seller=True).count()
    total_seller_revenue = 0
    total_seller_products = 0
    total_seller_orders = 0
    for sd in seller_data:
        total_seller_revenue += sd['total_revenue']
        total_seller_products += sd['product_count']
        total_seller_orders += sd['total_orders']

    context = {
        'sellers': page_obj,
        'page_obj': page_obj,
        'total_sellers': total_sellers,
        'total_seller_revenue': total_seller_revenue,
        'total_seller_products': total_seller_products,
        'total_seller_orders': total_seller_orders,
        'current_search': search,
        'current_sort': sort,
        'current_verified': verified_filter,
    }
    return render(request, 'store/admin_sellers.html', context)


# ==============================================================================
# SECTION: Admin Seller Detail
# ==============================================================================

@staff_member_required
def admin_seller_detail(request, seller_id):
    seller = get_object_or_404(User, id=seller_id)
    profile = get_object_or_404(Profile, user=seller, is_seller=True)

    products = Product.objects.filter(seller=seller).order_by('-created_at')

    search = request.GET.get('search', '').strip()
    stock_filter = request.GET.get('stock', '')
    if search:
        products = products.filter(name__icontains=search)
    if stock_filter == 'low':
        products = products.filter(stock__gt=0, stock__lt=5)
    elif stock_filter == 'out':
        products = products.filter(stock=0)

    product_paginator = Paginator(products, 15)
    prod_page = request.GET.get('page', 1)
    prod_page_obj = product_paginator.get_page(prod_page)

    seller_order_items = OrderItem.objects.filter(product__in=Product.objects.filter(seller=seller).values('id'))
    total_revenue = seller_order_items.aggregate(t=Sum('price'))['t'] or 0
    total_units = seller_order_items.aggregate(t=Sum('quantity'))['t'] or 0
    total_orders = seller_order_items.values('order').distinct().count()
    pending_orders = Order.objects.filter(id__in=seller_order_items.values('order_id'), status='Pending').count()
    completed_orders = Order.objects.filter(id__in=seller_order_items.values('order_id'), status='Delivered').count()

    top_products = seller_order_items.values('product__name', 'product_id').annotate(
        total_sold=Sum('quantity'), total_earned=Sum('price')
    ).order_by('-total_sold')[:10]

    recent_orders = Order.objects.filter(
        id__in=seller_order_items.values('order_id')
    ).order_by('-created_at')[:10]

    monthly_revenue = seller_order_items.annotate(
        month=TruncMonth('order__created_at')
    ).values('month').annotate(
        total=Sum('price')
    ).order_by('month')

    context = {
        'seller': seller,
        'profile': profile,
        'products': prod_page_obj,
        'prod_page_obj': prod_page_obj,
        'total_revenue': total_revenue,
        'total_units': total_units,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'product_count': Product.objects.filter(seller=seller).count(),
        'top_products': top_products,
        'recent_orders': recent_orders,
        'monthly_revenue': list(monthly_revenue),
        'current_search': search,
        'current_stock': stock_filter,
    }
    return render(request, 'store/admin_seller_detail.html', context)


# ==============================================================================
# SECTION: Newsletter — Broadcast
# ==============================================================================

@staff_member_required
def admin_newsletter_broadcast(request):
    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '').strip()
        cta_text = request.POST.get('cta_text', '').strip()
        cta_url = request.POST.get('cta_url', '').strip()

        if not subject or not body:
            messages.error(request, "Subject and body are required.")
            return redirect('store:admin_newsletter_broadcast')

        subscribers = NewsletterSubscriber.objects.filter(active=True)
        sent = 0
        errors = 0
        for sub in subscribers:
            try:
                ctx = {
                    'subject': subject,
                    'body': body,
                    'cta_text': cta_text,
                    'cta_url': cta_url,
                    'token': sub.token,
                    'subscriber_name': '',
                    'base_url': settings.BASE_URL,
                    'current_year': timezone.now().year,
                }
                html = render_to_string('store/newsletter_broadcast_email.html', ctx)
                text = render_to_string('store/newsletter_broadcast_email.txt', ctx)
                send_mail(subject, text, settings.DEFAULT_FROM_EMAIL,
                          [sub.email], html_message=html)
                sent += 1
            except Exception:
                errors += 1

        log_action(request.user, 'newsletter_broadcast',
                   f"Broadcast sent to {sent} subscribers ({errors} failed)",
                   {'subject': subject, 'sent': sent, 'errors': errors}, request)
        messages.success(request, f"Broadcast sent to {sent} subscribers ({errors} failed).")
        return redirect('store:admin_dashboard')

    return render(request, 'store/admin_newsletter_broadcast.html')


# ==============================================================================
# SECTION: Newsletter — Subscriber Management
# ==============================================================================

@staff_member_required
def admin_manage_subscribers(request):
    subscribers = NewsletterSubscriber.objects.all().order_by('-subscribed_at')

    search = request.GET.get('q', '').strip()
    if search:
        subscribers = subscribers.filter(email__icontains=search)

    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        subscribers = subscribers.filter(active=True)
    elif status_filter == 'inactive':
        subscribers = subscribers.filter(active=False)

    paginator = Paginator(subscribers, 50)
    page = request.GET.get('page', 1)
    subscribers_page = paginator.get_page(page)

    if request.method == 'POST':
        action = request.POST.get('action', '')
        sub_id = request.POST.get('subscriber_id', '')
        sub = get_object_or_404(NewsletterSubscriber, id=sub_id)
        if action == 'toggle':
            sub.active = not sub.active
            sub.save(update_fields=['active'])
            status = 'activated' if sub.active else 'deactivated'
            messages.success(request, f"{sub.email} {status}.")
        elif action == 'delete':
            sub.delete()
            messages.success(request, f"{sub.email} deleted.")
        return redirect('store:admin_manage_subscribers')

    context = {
        'subscribers': subscribers_page,
        'current_search': search,
        'current_status': status_filter,
        'total_count': NewsletterSubscriber.objects.count(),
    }
    return render(request, 'store/admin_manage_subscribers.html', context)
