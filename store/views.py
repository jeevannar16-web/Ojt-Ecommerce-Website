from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# 💡 LOCAL IMPORT: Use a dot (.) because these models live in this exact 'store' app folder!
from .models import Product, CartItem, Order, OrderItem

# 1. AJAX View: Add Item to Cart
def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Please log in first.'}, status=401)
        
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        
        # Get or create the cart item for this user
        cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
        if not created:
            cart_item.quantity += 1
            cart_item.save()
            
        return JsonResponse({'success': True, 'message': 'Product added to cart!'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)

# 2. Page View: Display Cart
@login_required
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    
    # Calculate the grand total price of everything inside the cart
    total_amount = sum(item.total_price for item in cart_items)
    
    context = {
        'cart_items': cart_items,
        'total_amount': total_amount,
    }
    # 💡 LOOKS INSIDE TEMPLATES/STORE/
    return render(request, 'store/cart.html', context)

# 3. Action View: Convert Cart Items into an Order (Checkout)
@login_required
def checkout_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    
    if not cart_items.exists():
        messages.error(request, "Your shopping cart is empty!")
        return redirect('cart')
        
    if request.method == 'POST':
        # 💡 Capture customer credentials and shipping metrics securely from form POST data
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        shipping_address = request.POST.get('shipping_address')
        city = request.POST.get('city')
        postal_code = request.POST.get('postal_code')
        
        # Simple Validation Check: Make sure they submitted their credentials
        if not all([full_name, shipping_address, city, phone_number]):
            messages.error(request, "Please fill out all required credentials and shipping locations.")
            return render(request, 'store/checkout.html', {'cart_items': cart_items})
            
        total_amount = sum(item.total_price for item in cart_items)
        
        # Create the order record
        order = Order.objects.create(
            user=request.user,
            full_name=full_name,
            email=email,
            shipping_address=f"{shipping_address}, {city} (ZIP: {postal_code})",
            total_amount=total_amount,
            status='Pending'
        )
        
        # Save individual line items securely
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.product.price,
                quantity=item.quantity
            )
            
        # Empty out the shopping cart
        cart_items.delete()
        
        messages.success(request, f"Thank you! Your order #{order.id} has been processed successfully.")
        return redirect('home')
        
    return render(request, 'store/checkout.html', {'cart_items': cart_items})








def product_list(request):  # or whatever your primary catalog view function is named
    """
    Renders the full inventory catalog and appends promotional 
    recommendation objects to the bottom shelf context.
    """
    products = Product.objects.all()
    
    # NEW: Query 4 random products to act as recommendations at the bottom
    recommendations = Product.objects.all().order_by('?')[:4]
    
    context = {
        'products': products,
        'recommendations': recommendations,  # Add this line to the context dictionary
        'title': 'Our Full Catalog'
    }
    return render(request, 'store/product_list.html', context)


def product_detail(request, product_id):
    """
    Displays an individual product's details alongside recommended items 
    filtered by matching category or item types.
    """
    product = get_object_or_404(Product, id=product_id)
    
    # 1. Primary Recommendation: Try finding other items in the same category
    recommendations = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    
    # 2. Fallback: If no other products match that category, show other items in the store so it's not empty
    if not recommendations.exists():
        recommendations = Product.objects.exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'recommendations': recommendations
    }
    return render(request, 'store/product_detail.html', context)




def sale_catalog(request):
    """
    Queries catalog items and routes cleanly to the dedicated catalog grid display page.
    """
    try:
        # Check for active promotion markdown filters
        products = Product.objects.filter(is_sale=True)
        if not products.exists():
            products = Product.objects.all()
    except Exception:
        products = Product.objects.all()

    # Automatically bundle recommendation objects for the bottom shelf grid layout
    recommendations = Product.objects.all().order_by('?')[:4]

    context = {
        'products': products,
        'recommendations': recommendations,
        'title': 'Flash Sale Collection',
        'is_sale_page': True
    }
    
    # CRITICAL FIX HERE: Ensure this points to 'store/product_list.html'
    return render(request, 'store/product_list.html', context)