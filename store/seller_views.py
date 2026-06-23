from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils.text import slugify
from .models import Product, ProductSize, Order, OrderItem, Category
from .activity_logger import log_action
from users.models import Profile, CredentialHistory
from django.core.paginator import Paginator
from django.contrib.auth.models import User


def _is_seller(user):
    return user.is_superuser or getattr(user, 'profile', None).is_seller

def _seller_products(user):
    if user.is_superuser:
        return Product.objects.all()
    return Product.objects.filter(seller=user)


def _parse_sizes(size_str):
    if not size_str or not size_str.strip():
        return []
    return [s.strip() for s in size_str.split(',') if s.strip()]


def seller_center(request):
    """Public seller center landing page."""
    seller_count = Profile.objects.filter(is_seller=True).count()
    product_count = Product.objects.count()
    order_count = Order.objects.count()
    return render(request, 'store/seller_center.html', {
        'seller_count': seller_count,
        'product_count': product_count,
        'order_count': order_count,
    })


@login_required
def seller_apply(request):
    """Dedicated seller application page with store details."""
    profile = request.user.profile

    if profile.is_seller:
        messages.info(request, "You are already a seller.")
        return redirect('store:seller_dashboard')

    if request.method == 'POST':
        store_name = request.POST.get('store_name', '').strip()
        business_type = request.POST.get('business_type', '').strip()
        phone = request.POST.get('phone', '').strip()
        store_description = request.POST.get('store_description', '').strip()

        errors = []
        if not store_name:
            errors.append("Store name is required.")
        if not business_type:
            errors.append("Please select a business type.")

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'store/seller/apply.html', {
                'form_data': request.POST,
            })

        business_reg = request.POST.get('business_registration', '').strip()
        tax_id_val = request.POST.get('tax_id', '').strip()
        business_addr = request.POST.get('business_address', '').strip()

        profile.store_name = store_name
        profile.store_slug = slugify(store_name) or f"store-{request.user.id}"
        profile.business_type = business_type
        profile.store_description = store_description
        profile.business_registration = business_reg
        profile.tax_id = tax_id_val
        profile.business_address = business_addr
        if 'id_proof' in request.FILES:
            profile.id_proof = request.FILES['id_proof']
        if phone:
            profile.phone = phone
        profile.seller_requested = True
        profile.seller_rejection_reason = ''
        from django.utils import timezone
        profile.seller_requested_at = timezone.now()
        profile.save()

        CredentialHistory.objects.create(
            user=request.user,
            store_name=store_name,
            business_type=business_type,
            store_description=store_description,
            business_registration=business_reg,
            tax_id=tax_id_val,
            business_address=business_addr,
            phone=phone,
        )

        log_action(request.user, 'seller_apply', f"Applied as seller — {store_name}",
                   {'store_name': store_name, 'business_type': business_type, 'phone': phone}, request)

        messages.success(
            request,
            "Your seller application has been submitted! An admin will review it shortly."
        )
        return redirect('profile')

    recent = CredentialHistory.objects.filter(user=request.user)[:5]
    return render(request, 'store/seller/apply.html', {
        'form_data': {
            'store_name': profile.store_name or '',
            'business_type': profile.business_type or '',
            'phone': profile.phone or '',
            'store_description': profile.store_description or '',
            'business_registration': profile.business_registration or '',
            'tax_id': profile.tax_id or '',
            'business_address': profile.business_address or '',
        },
        'recent_credentials': recent,
    })


def seller_storefront(request, slug):
    """Public storefront for a seller — Daraz-style."""
    profile = get_object_or_404(Profile, store_slug=slug, is_seller=True)
    seller = profile.user

    products = Product.objects.filter(seller=seller, stock__gt=0)

    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)

    search = request.GET.get('search', '').strip()
    if search:
        products = products.filter(name__icontains=search)

    sort = request.GET.get('sort', 'newest')
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'name':
        products = products.order_by('name')
    else:
        products = products.order_by('-created_at')

    total_products = products.count()
    categories = set(Product.objects.filter(seller=seller)
                     .exclude(category__isnull=True)
                     .values_list('category__id', 'category__name'))

    return render(request, 'store/seller/storefront.html', {
        'store_profile': profile,
        'seller': seller,
        'products': products,
        'total_products': total_products,
        'categories': sorted(categories, key=lambda x: x[1] or ''),
        'current_category': category_id,
        'current_sort': sort,
        'current_search': search,
    })


@login_required
def seller_dashboard(request):
    if not _is_seller(request.user):
        messages.error(request, "You do not have seller access.")
        return redirect('home')

    products = _seller_products(request.user)
    total_products = products.count()
    low_stock = products.filter(stock__lt=5).count()
    out_of_stock = products.filter(stock=0).count()

    seller_order_items = OrderItem.objects.filter(product__in=products.values('id'))
    total_orders = seller_order_items.values('order').distinct().count()
    total_revenue = seller_order_items.aggregate(t=Sum('price'))['t'] or 0
    total_units_sold = seller_order_items.aggregate(t=Sum('quantity'))['t'] or 0

    seller_order_ids = seller_order_items.values_list('order_id', flat=True).distinct()
    pending_orders = Order.objects.filter(id__in=seller_order_ids, status='Pending').count()
    completed_orders = Order.objects.filter(id__in=seller_order_ids, status='Delivered').count()

    top_products = seller_order_items.values('product__name', 'product_id').annotate(
        total_sold=Sum('quantity'),
        total_earned=Sum('price')
    ).order_by('-total_sold')[:5]

    recent_orders_list = Order.objects.filter(
        id__in=seller_order_ids
    ).order_by('-created_at')[:5]

    recent_products = products.order_by('-created_at')[:5]

    context = {
        'total_products': total_products,
        'low_stock': low_stock,
        'out_of_stock': out_of_stock,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_units_sold': total_units_sold,
        'revenue_per_unit': total_revenue / total_units_sold if total_units_sold > 0 else 0,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'top_products': top_products,
        'recent_orders': recent_orders_list,
        'recent_products': recent_products,
    }
    return render(request, 'store/seller/dashboard.html', context)


@login_required
def seller_product_list(request):
    if not _is_seller(request.user):
        messages.error(request, "You do not have seller access.")
        return redirect('home')

    products = _seller_products(request.user).order_by('-created_at')

    stock_filter = request.GET.get('stock', '')
    if stock_filter == 'out':
        products = products.filter(stock=0)
    elif stock_filter == 'low':
        products = products.filter(stock__gt=0, stock__lt=5)

    paginator = Paginator(products, 20)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)

    return render(request, 'store/seller/product_list.html', {
        'products': page_obj,
        'page_obj': page_obj,
        'stock_filter': stock_filter,
    })


@login_required
def seller_product_add(request):
    if not _is_seller(request.user):
        messages.error(request, "You do not have seller access.")
        return redirect('home')

    categories = Category.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        stock = request.POST.get('stock', 0)
        description = request.POST.get('description', '').strip()
        sizes_raw = request.POST.get('sizes', '').strip()
        is_sale = request.POST.get('is_sale') == 'on'

        errors = []
        if not name:
            errors.append("Product name is required.")
        if not price:
            errors.append("Price is required.")
        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, 'store/seller/product_form.html', {
                'categories': categories,
                'form_data': request.POST,
            })

        product = Product(
            seller=request.user,
            name=name,
            category_id=category_id or None,
            price=price,
            stock=stock,
            description=description,
            size=sizes_raw or None,
            is_sale=is_sale,
        )

        if 'image' in request.FILES:
            product.image = request.FILES['image']

        product.save()

        size_names = _parse_sizes(sizes_raw)
        if size_names:
            for sz in size_names:
                ProductSize.objects.create(product=product, size=sz, stock=0)
            product.stock = 0
            product.save(update_fields=['stock'])

        log_action(request.user, 'product_create', f"Created product '{name}'",
                   {'product_id': product.id, 'product_name': name, 'price': price, 'category_id': category_id}, request)
        messages.success(request, f"Product '{name}' created successfully!")
        return redirect('store:seller_product_list')

    return render(request, 'store/seller/product_form.html', {
        'categories': categories,
    })


@login_required
def seller_product_edit(request, product_id):
    if not _is_seller(request.user):
        messages.error(request, "You do not have seller access.")
        return redirect('home')

    product = get_object_or_404(Product, id=product_id)
    if not request.user.is_superuser and product.seller != request.user:
        messages.error(request, "You can only edit your own products.")
        return redirect('store:seller_product_list')

    categories = Category.objects.all()

    if request.method == 'POST':
        product.name = request.POST.get('name', product.name).strip()
        product.category_id = request.POST.get('category') or None
        product.price = request.POST.get('price', product.price)
        product.description = request.POST.get('description', '').strip()
        sizes_raw = request.POST.get('sizes', '').strip()
        product.is_sale = request.POST.get('is_sale') == 'on'
        product.is_featured = request.POST.get('is_featured') == 'on'

        if 'image' in request.FILES:
            product.image = request.FILES['image']

        new_size_names = _parse_sizes(sizes_raw)
        if new_size_names:
            existing = set(product.sizes.values_list('size', flat=True))
            incoming = set(new_size_names)
            for sz in incoming - existing:
                ProductSize.objects.create(product=product, size=sz, stock=0)
            for sz in existing - incoming:
                product.sizes.filter(size=sz).delete()
        else:
            product.sizes.all().delete()

        product.size = sizes_raw or None
        product.save()
        log_action(request.user, 'product_update', f"Updated product '{product.name}'",
                   {'product_id': product.id, 'product_name': product.name}, request)
        messages.success(request, f"Product '{product.name}' updated!")
        return redirect('store:seller_product_list')

    existing_sizes = ', '.join(product.sizes.values_list('size', flat=True))
    return render(request, 'store/seller/product_form.html', {
        'product': product,
        'categories': categories,
        'form_data': {
            'name': product.name,
            'category': product.category_id,
            'price': product.price,
            'description': product.description,
            'sizes': existing_sizes or product.size or '',
            'is_sale': product.is_sale,
            'is_featured': product.is_featured,
        }
    })


@login_required
def seller_product_delete(request, product_id):
    if not _is_seller(request.user):
        messages.error(request, "You do not have seller access.")
        return redirect('home')

    product = get_object_or_404(Product, id=product_id)
    if not request.user.is_superuser and product.seller != request.user:
        messages.error(request, "You can only delete your own products.")
        return redirect('store:seller_product_list')

    if request.method == 'POST':
        name = product.name
        log_action(request.user, 'product_delete', f"Deleted product '{name}'",
                   {'product_id': product.id, 'product_name': name}, request)
        product.delete()
        messages.success(request, f"Product '{name}' deleted.")
    return redirect('store:seller_product_list')


@login_required
def seller_orders(request):
    if not _is_seller(request.user):
        messages.error(request, "You do not have seller access.")
        return redirect('home')

    seller_product_ids = _seller_products(request.user).values('id')
    order_items = OrderItem.objects.filter(product__in=seller_product_ids).select_related('order', 'product').order_by('-order__created_at')

    status_filter = request.GET.get('status', '')
    if status_filter:
        order_items = order_items.filter(order__status=status_filter)

    paginator = Paginator(order_items, 20)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)

    return render(request, 'store/seller/orders.html', {
        'page_obj': page_obj,
        'order_items': page_obj,
        'current_status': status_filter,
    })
