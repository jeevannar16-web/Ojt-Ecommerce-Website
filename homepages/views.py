"""Homepage and static page views."""

import random
import datetime
from django.shortcuts import render
from django.db import models
from django.db.models import Q, Count, Sum
from django.views.generic import TemplateView

from store.models import Product, Category, OrderItem, CartItem
from users.models import Profile


def home(request):
    base_qs = Product.objects.select_related('category')
    categories = Category.objects.annotate(pcount=Count('products'))
    error = None

    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    image = request.FILES.get('image_file')

    featured_products = base_qs.filter(is_featured=True)

    search_results = Product.objects.none()
    is_searching = False

    if image or query or category_id:
        is_searching = True
        if image:
            filename = image.name.lower()
            if 'nike' in filename:
                search_results = base_qs.filter(name__icontains='nike')
            elif 'jordan' in filename:
                search_results = base_qs.filter(name__icontains='jordan')
            elif 'flower' in filename or 'sunflower' in filename:
                search_results = base_qs.filter(name__icontains='flower')
            elif any(word in filename for word in ['shoe', 'sneaker', 'adidas']):
                search_results = base_qs.filter(name__icontains='shoe') | base_qs.filter(name__icontains='sneaker')
            else:
                error = f"No visual matches found for '{image.name}'."
                search_results = Product.objects.none()
        elif query:
            search_term = query.lower()
            search_variants = [search_term]
            if search_term.endswith('s') and len(search_term) > 3:
                search_variants.append(search_term[:-1])
            else:
                search_variants.append(search_term + 's')
            query_filter = Q()
            for variant in search_variants:
                query_filter |= Q(name__icontains=variant) | Q(category__name__icontains=variant)
            search_results = base_qs.filter(query_filter).distinct()
            if not search_results.exists():
                error = f"No items found matching '{query}'."
                search_results = Product.objects.none()
        elif category_id:
            search_results = base_qs.filter(category_id=category_id)

    # ─── DYNAMIC HOMEPAGE SECTIONS ──────────────────────────────
    today = datetime.date.today()
    seed = today.toordinal()
    rng = random.Random(seed)

    all_product_ids = set(Product.objects.values_list('id', flat=True))
    used_ids = set()

    def pick_products(queryset, count, exclude=None):
        ids = list(queryset.values_list('id', flat=True))
        if exclude:
            ids = [i for i in ids if i not in exclude]
        rng.shuffle(ids)
        chosen = ids[:count]
        return list(base_qs.filter(id__in=chosen))

    def mark_used(products):
        for p in products:
            used_ids.add(p.id)

    # 1. Flash Sale
    on_sale = pick_products(base_qs.filter(is_sale=True), 12, used_ids)
    mark_used(on_sale)

    # 2. Best Deals
    best_qs = base_qs.filter(
        original_price__isnull=False, original_price__gt=models.F('price')
    )
    best_ids = [p.id for p in best_qs if p.discount_percent >= 10]
    rng.shuffle(best_ids)
    best_ids = [i for i in best_ids if i not in used_ids][:12]
    best_deals = list(base_qs.filter(id__in=best_ids))
    mark_used(best_deals)

    # 3. Top Rated
    top_qs = base_qs.exclude(rating=0.0)
    top_rated = pick_products(top_qs, 12, used_ids)
    mark_used(top_rated)

    # 4. New Arrivals
    recent_qs = base_qs.order_by('-created_at')[:50]
    new_arrivals = pick_products(recent_qs, 12, used_ids)
    mark_used(new_arrivals)

    # 5. Value Deals
    cheap_qs = base_qs.order_by('price')[:50]
    low_price = pick_products(cheap_qs, 12, used_ids)
    mark_used(low_price)

    # 6. Almost Gone
    low_stock_qs = base_qs.filter(stock__gt=0, stock__lt=5)
    low_stock_items = pick_products(low_stock_qs, 12, used_ids)
    mark_used(low_stock_items)

    # 7. Trending Now
    trending_ids = (
        OrderItem.objects.values('product_id')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')[:20]
    )
    trend_pids = [t['product_id'] for t in trending_ids if t['product_id'] not in used_ids]
    rng.shuffle(trend_pids)
    trending_ids_final = trend_pids[:12]
    trending = list(base_qs.filter(id__in=trending_ids_final))
    if not trending:
        trending = pick_products(base_qs.all(), 12, used_ids)
    mark_used(trending)

    # 8. Category Sections
    top_cats = categories.order_by('-pcount')[:6]
    category_sections = []
    for cat in top_cats:
        prods = pick_products(base_qs.filter(category=cat), 10, used_ids)
        if prods:
            category_sections.append({'category': cat, 'products': prods})
            mark_used(prods)

    # 9. Banner
    banner_qs = (
        base_qs.filter(is_featured=True, is_sale=True) |
        base_qs.filter(is_featured=True)
    ).distinct()
    banner_products = pick_products(banner_qs, 8, set())
    rng.shuffle(banner_products)

    # 10. Personalized recommendations (authenticated only — not cached)
    recommendations = []
    user = request.user
    if user.is_authenticated:
        interest_cat_ids = set()
        cart_cats = CartItem.objects.filter(user=user).values_list('product__category_id', flat=True)
        interest_cat_ids.update(cart_cats)
        order_cats = OrderItem.objects.filter(order__user=user).values_list('product__category_id', flat=True)
        interest_cat_ids.update(order_cats)
        from store.models import FavoriteItem
        fav_cats = FavoriteItem.objects.filter(user=user).values_list('product__category_id', flat=True)
        interest_cat_ids.update(fav_cats)

        if interest_cat_ids:
            rec_qs = base_qs.filter(category_id__in=interest_cat_ids)
            recommendations = pick_products(rec_qs, 8, used_ids)
        if not recommendations:
            recommendations = base_qs.filter(is_featured=True)[:4]
    else:
        recommendations = base_qs.filter(is_featured=True)[:4]

    top_selling = list(
        base_qs.filter(
            id__in=OrderItem.objects.values('product_id')
            .annotate(total=Count('id'))
            .filter(total__gt=0)
            .order_by('-total')[:8]
            .values('product_id')
        )
    )
    rng.shuffle(top_selling)

    seller_count = Profile.objects.filter(is_seller=True).count()
    total_seller_products = Product.objects.exclude(seller__isnull=True).count()
    seller_revenue = OrderItem.objects.filter(
        product__seller__isnull=False
    ).aggregate(t=Sum('price'))['t'] or 0

    recent_convs = []
    if user.is_authenticated:
        from store.models import Conversation
        conv_qs = Conversation.objects.filter(
            Q(customer=user) | Q(seller=user)
        ).select_related('customer', 'seller', 'product').prefetch_related('messages').order_by('-updated_at')[:6]
        for c in conv_qs:
            last = c.last_message()
            other = c.seller if c.customer == user else c.customer
            recent_convs.append({
                'conv': c,
                'last_message': last,
                'unread': c.unread_count(user),
                'other_user': other,
                'is_support': other.is_staff or other.is_superuser,
                'other_status_emoji': getattr(other.profile, 'status_emoji', '') if hasattr(other, 'profile') else '',
                'other_status_text': getattr(other.profile, 'status_text', 'Available') if hasattr(other, 'profile') else 'Available',
                'product': c.product,
                'store_slug': getattr(other.profile, 'store_slug', '') if hasattr(other, 'profile') else '',
            })

    context = {
        'categories': categories,
        'featured_products': featured_products,
        'search_results': search_results,
        'recommendations': recommendations,
        'is_searching': is_searching,
        'search_query': query,
        'search_error': error,
        'new_arrivals': new_arrivals,
        'top_rated': top_rated,
        'on_sale': on_sale,
        'low_price': low_price,
        'low_stock_items': low_stock_items,
        'banner_products': banner_products,
        'category_sections': category_sections,
        'best_deals': best_deals,
        'trending': trending,
        'top_selling': top_selling,
        'seller_count': seller_count,
        'total_seller_products': total_seller_products,
        'seller_revenue': seller_revenue,
        'recent_conversations': recent_convs,
    }
    return render(request, 'index.html', context)



class PrivacyPolicyView(TemplateView):
    template_name = 'homepages/privacy.html'


class TermsOfServiceView(TemplateView):
    template_name = 'homepages/terms.html'


class CookiesPolicyView(TemplateView):
    template_name = 'homepages/cookies.html'
