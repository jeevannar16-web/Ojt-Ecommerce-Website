from django.shortcuts import render
from store.models import Product, Category # 💡 Make sure Category is imported!

def home(request):
    # Fetch categories and featured products
    categories = Category.objects.all()
    featured_products = Product.objects.filter(is_featured=True)
    
    # Check if the user clicked a specific category filter link
    category_id = request.GET.get('category')
    if category_id:
        featured_products = Product.objects.filter(category_id=category_id)

    context = {
        'categories': categories,
        'featured_products': featured_products,
    }
    return render(request, 'index.html', context)