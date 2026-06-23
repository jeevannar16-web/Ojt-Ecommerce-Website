from django.shortcuts import render
from django.db.models import Q
from django.views.generic import TemplateView
from store.models import Product, Category

def home(request):
    categories = Category.objects.all()
    error = None

    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    image = request.FILES.get('image_file')

    featured_products = Product.objects.filter(is_featured=True)
    recommendations = Product.objects.filter(is_featured=True)[:4]

    search_results = Product.objects.none()
    is_searching = False

    if image or query or category_id:
        is_searching = True
        if image:
            filename = image.name.lower()
            if 'nike' in filename:
                search_results = Product.objects.filter(name__icontains='nike')
            elif 'jordan' in filename:
                search_results = Product.objects.filter(name__icontains='jordan')
            elif 'flower' in filename or 'sunflower' in filename:
                search_results = Product.objects.filter(name__icontains='flower')
            elif any(word in filename for word in ['shoe', 'sneaker', 'adidas']):
                search_results = Product.objects.filter(name__icontains='shoe') | Product.objects.filter(name__icontains='sneaker')
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
            search_results = Product.objects.filter(query_filter).distinct()
            if not search_results.exists():
                error = f"No items found matching '{query}'."
                search_results = Product.objects.none()
        elif category_id:
            search_results = Product.objects.filter(category_id=category_id)

    # --- Dynamic Homepage Sections ---
    new_arrivals = Product.objects.all().order_by('-created_at')[:12]

    top_rated = Product.objects.exclude(rating=0.0).order_by('-rating')[:12]

    on_sale = Product.objects.filter(is_sale=True)[:12]

    low_price = Product.objects.all().order_by('price')[:12]

    low_stock_items = Product.objects.filter(stock__gt=0, stock__lt=5).order_by('stock')[:12]

    banner_products = (
        Product.objects.filter(is_featured=True, is_sale=True) |
        Product.objects.filter(is_featured=True)
    ).distinct().order_by('-rating')[:8]

    # Top 6 categories by product count with their products
    from django.db.models import Count
    top_cats = Category.objects.annotate(pcount=Count('products')).order_by('-pcount')[:6]
    category_sections = []
    for cat in top_cats:
        prods = Product.objects.filter(category=cat)[:10]
        if prods:
            category_sections.append({'category': cat, 'products': prods})

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
    }
    return render(request, 'index.html', context)


class PrivacyPolicyView(TemplateView):
    template_name = 'homepages/privacy.html'


class TermsOfServiceView(TemplateView):
    template_name = 'homepages/terms.html'


class CookiesPolicyView(TemplateView):
    template_name = 'homepages/cookies.html'
