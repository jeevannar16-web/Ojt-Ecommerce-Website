from django.shortcuts import render
from django.db.models import Q  
from django.views.generic import TemplateView
from store.models import Product, Category

def home(request):
    categories = Category.objects.all()
    error = None

    # Capture clean search variables
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    image = request.FILES.get('image_file')

    # Initialize defaults
    featured_products = Product.objects.filter(is_featured=True)
    recommendations = Product.objects.filter(is_featured=True)[:4]
    
    # 💡 Establish absolute base defaults to avoid template fallback confusion
    search_results = Product.objects.none()
    is_searching = False

    # Check if any search or filtering action is occurring
    if image or query or category_id:
        is_searching = True
        
        # 1. Visual Search Filter Process Pipeline
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
                
        # 2. Text Search Filter Process Pipeline
        elif query:
            search_term = query.lower()
            search_variants = [search_term]
            
            # Explicit singular/plural word pairing bounds
            if search_term.endswith('s') and len(search_term) > 3:
                search_variants.append(search_term[:-1])  # e.g., 'shoes' -> 'shoe'
            else:
                search_variants.append(search_term + 's')  # e.g., 'shoe' -> 'shoes'

            # Build a precise conditional filter across names and categories
            query_filter = Q()
            for variant in search_variants:
                query_filter |= Q(name__icontains=variant) | Q(category__name__icontains=variant)
            
            search_results = Product.objects.filter(query_filter).distinct()
            
            if not search_results.exists():
                error = f"No items found matching '{query}'."
                search_results = Product.objects.none()
                
        # 3. Category Sidebar Click Filter Pipeline
        elif category_id:
            search_results = Product.objects.filter(category_id=category_id)

    context = {
        'categories': categories,
        'featured_products': featured_products,
        'search_results': search_results,       
        'recommendations': recommendations,     
        'is_searching': is_searching,  # 💡 Trusted template rendering flag
        'search_query': query,
        'search_error': error,
    }
    return render(request, 'index.html', context)


class PrivacyPolicyView(TemplateView):
    template_name = 'homepages/privacy.html'


class TermsOfServiceView(TemplateView):
    template_name = 'homepages/terms.html'


class CookiesPolicyView(TemplateView):
    template_name = 'homepages/cookies.html'