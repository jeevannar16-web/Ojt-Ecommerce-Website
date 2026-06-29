"""Product listing and detail views."""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from ..models import Category, Product, FavoriteItem, Review, OrderItem
from django.db.models import Count, Avg


# SEARCH & PRODUCT LISTING
GOAL_MAP = {
    'muscle': ['Muscle & Strength', 'Dumbbell Training', 'Kettlebell Workouts', 'Gym Machines'],
    'home':   ['Resistance Bands', 'Yoga & Pilates', 'Bodyweight Calisthenics'],
    'loss':   ['Weight Loss', 'Cardio Training', 'Resistance Bands'],
    'cardio': ['Cardio Training', 'Outdoor Adventure', 'Mobility Training'],
}

GOAL_LABELS = {
    'muscle': 'Build Muscle',
    'home':   'Home Gym',
    'loss':   'Weight Loss',
    'cardio': 'Cardio',
}

SORT_MAP = {
    'price_asc':   'price',
    'price_desc':  '-price',
    'rating_desc': '-rating',
    'name_asc':    'name',
    'newest':      '-id',
}



def _filter_and_sort_products(request):
    products = Product.objects.select_related('category').all()
    title = "Our Full Catalog"
    is_search = False

    category_id = request.GET.get('category')
    if category_id:
        try:
            products = products.filter(category_id=int(category_id))
            cat = Category.objects.filter(id=int(category_id)).first()
            if cat:
                title = f"Elite {cat.name} Collection"
        except (ValueError, TypeError):
            pass

    search_query = request.GET.get('search', '').strip()
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
        title = f'Search Results for "{search_query}"'
        is_search = True

    price_min = request.GET.get('price_min', '').strip()
    price_max = request.GET.get('price_max', '').strip()
    if price_min:
        try:
            products = products.filter(price__gte=float(price_min))
        except ValueError:
            pass
    if price_max:
        try:
            products = products.filter(price__lte=float(price_max))
        except ValueError:
            pass

    selected_types = request.GET.getlist('type')
    if selected_types:
        products = products.filter(category__name__in=selected_types)

    only_available = request.GET.get('available') == '1'
    if only_available:
        products = products.filter(stock__gt=0)

    goal = request.GET.get('goal', '').strip()
    if goal and goal in GOAL_MAP:
        products = products.filter(category__name__in=GOAL_MAP[goal])

    sort = request.GET.get('sort', '')
    if sort in SORT_MAP:
        products = products.order_by(SORT_MAP[sort])
    else:
        products = products.order_by('id')

    products = products.distinct()

    return products, title, is_search, category_id, goal, sort, price_min, price_max, selected_types, only_available, search_query



@vary_on_cookie
@cache_page(300, key_prefix='products')
def product_list(request):
    products, title, is_search, category_id, goal, sort, price_min, price_max, selected_types, only_available, search_query = _filter_and_sort_products(request)

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    filtered_category_ids = products.values('category_id').distinct()
    all_categories = Category.objects.filter(id__in=filtered_category_ids)

    filtered_cat_ids_list = [c['category_id'] for c in filtered_category_ids if c['category_id']]
    if filtered_cat_ids_list:
        recommendations = Product.objects.filter(category_id__in=filtered_cat_ids_list).order_by('-created_at')[:4]
    else:
        recommendations = Product.objects.filter(is_featured=True)[:4]
    if not recommendations.exists():
        recommendations = Product.objects.order_by('-created_at')[:4]

    all_category_names = set(Category.objects.filter(products__isnull=False).values_list('name', flat=True))
    active_goals = []
    for g_key, g_cats in GOAL_MAP.items():
        if any(cat_name in all_category_names for cat_name in g_cats):
            active_goals.append({
                'key': g_key,
                'label': GOAL_LABELS.get(g_key, g_key.title()),
                'categories': g_cats,
            })

    context = {
        'products': page_obj,
        'page_obj': page_obj,
        'total_count': paginator.count,
        'recommendations': recommendations,
        'title': title,
        'is_search': is_search,
        'all_categories': all_categories,
        'selected_types': selected_types,
        'price_min': price_min,
        'price_max': price_max,
        'only_available': only_available,
        'active_goal': goal,
        'active_goals': active_goals,
        'active_category_id': category_id or '',
        'active_sort': sort,
        'search_query': search_query,
    }
    return render(request, 'store/product_list.html', context)



def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    recommendations = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:4]
    
    if not recommendations.exists():
        recommendations = Product.objects.exclude(id=product.id)[:4]

    is_favorited = False
    user_review = None
    has_purchased = False

    if request.user.is_authenticated:
        is_favorited = FavoriteItem.objects.filter(
            user=request.user, 
            product=product
        ).exists()
        
        user_review = Review.objects.filter(
            user=request.user, 
            product=product
        ).first()
        
        has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            order__status='Delivered',
            product=product
        ).exists()

    reviews = Review.objects.filter(
        product=product
    ).select_related('user').order_by('-created_at')
    
    total_reviews = reviews.count()

    rating_counts = reviews.values('rating').annotate(count=Count('id'))
    counts_dict = {item['rating']: item['count'] for item in rating_counts}

    rating_breakdown = {}
    for i in range(1, 6):
        count = counts_dict.get(i, 0)
        percentage = round((count / total_reviews) * 100) if total_reviews > 0 else 0
        rating_breakdown[i] = {
            'count': count,
            'percentage': percentage
        }

    sizes = product.sizes.all()
    if not sizes.exists() and product.size:
        size_list = [sz.strip() for sz in product.size.split(',') if sz.strip()]
    else:
        size_list = []

    context = {
        'product': product,
        'recommendations': recommendations,
        'is_favorited': is_favorited,
        'reviews': reviews,
        'total_reviews': total_reviews,
        'user_review': user_review,
        'has_purchased': has_purchased,
        'rating_breakdown': rating_breakdown,
        'sizes': sizes,
        'size_list': size_list,
    }
    return render(request, 'store/product_detail.html', context)


def product_list_api(request):
    products, title, is_search, category_id, goal, sort, price_min, price_max, selected_types, only_available, search_query = _filter_and_sort_products(request)

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    cards_html = ''
    for idx, product in enumerate(page_obj):
        cards_html += render_to_string('partials/product_card.html', {
            'product': product,
            'index': idx + 1,
        })

    return JsonResponse({
        'cards_html': cards_html,
        'has_next': page_obj.has_next(),
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        'total': paginator.count,
        'loaded': len(page_obj.object_list),
        'is_search': is_search,
        'search_query': search_query,
    })


def sale_catalog(request):
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    active_sort = request.GET.get('sort', '')

    products = Product.objects.filter(is_sale=True).order_by('id')
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    recommendations = Product.objects.filter(is_featured=True)[:4]

    context = {
        'products': page_obj,
        'page_obj': page_obj,
        'total_count': paginator.count,
        'recommendations': recommendations,
        'title': 'Flash Sale Collection',
        'is_sale_page': True,
        'price_min': price_min,
        'price_max': price_max,
        'active_sort': active_sort,
        'is_search': False,
        'search_query': '',
    }
    return render(request, 'store/product_list.html', context)



def product_stock_api(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
    sizes_data = []
    if product.has_sizes:
        for ps in product.sizes.all():
            sizes_data.append({'size': ps.size, 'stock': ps.stock})
    response = JsonResponse({
        'stock_remaining': product.stock,
        'has_sizes': product.has_sizes,
        'sizes': sizes_data,
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def search_suggestions(request):
    q = request.GET.get('q', '').strip()
    products = Product.objects.all()
    if q:
        products = products.filter(name__icontains=q)
    products = products.values('id', 'name', 'price')[:5]
    return JsonResponse({'products': list(products)})
