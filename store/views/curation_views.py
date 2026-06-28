"""Product curation views."""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
import base64
from ..models import Product


# PRODUCT CURATION & IMAGE MANAGEMENT
def curation_workspace(request):
    """Display the curation workspace with a single product - ALLOW EDITING ANYTIME."""
    current_id = request.GET.get('id')
    
    if current_id:
        try:
            product = Product.objects.get(id=current_id)
        except Product.DoesNotExist:
            product = None
    else:
        product = Product.objects.order_by('id').first()

    prev_product = None
    next_product = None
    
    if product:
        prev_product = Product.objects.filter(id__lt=product.id).order_by('-id').first()
        next_product = Product.objects.filter(id__gt=product.id).order_by('id').first()

    total = Product.objects.count()
    curated = Product.objects.exclude(image='').exclude(image__isnull=True).count()

    current_position = 0
    if product:
        current_position = Product.objects.filter(id__lte=product.id).count()

    context = {
        'product': product,
        'prev_product': prev_product,
        'next_product': next_product,
        'total': total,
        'curated': curated,
        'current_position': current_position,
    }
    
    print(f"\nCuration Workspace - Product {product.id if product else 'None'}")
    print(f"   Position: {current_position}/{total} | Curated: {curated}")
    
    return render(request, 'store/curation.html', context)



@csrf_exempt
def update_curation_asset(request):
    """
    Handle image upload and save it to the product.
    Allows editing anytime, even if already curated.
    """
    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "error": "Invalid request method"
        }, status=405)

    try:
        product_id = request.POST.get('id')
        image_data = request.POST.get('image')
        target_type = request.POST.get('target_type', 'product')

        if not product_id or not image_data:
            return JsonResponse({
                "success": False,
                "error": "Missing product ID or image data"
            }, status=400)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "Product not found"
            }, status=404)

        if not image_data.startswith('data:image'):
            return JsonResponse({
                "success": False,
                "error": "Invalid image format"
            }, status=400)

        try:
            format_part, imgstr = image_data.split(';base64,')
            ext = format_part.split('/')[-1].lower()

            valid_extensions = ['png', 'jpg', 'jpeg', 'gif', 'webp']

            if ext not in valid_extensions:
                return JsonResponse({
                    "success": False,
                    "error": f"Unsupported format: {ext}"
                }, status=400)

            raw_binary_file = ContentFile(
                base64.b64decode(imgstr)
            )

        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": f"Image decode error: {str(e)}"
            }, status=400)

        if target_type == 'category' and product.category:
            category = product.category
            file_name = f"curated_cat_{category.id}.{ext}"
            category.image.save(file_name, raw_binary_file, save=True)
            print(f"Updated category image: {file_name}")
        else:
            file_name = f"curated_prod_{product.id}.{ext}"
            product.image.save(file_name, raw_binary_file, save=True)
            product.save()
            print(f"Updated product image: {file_name}")

        next_product = Product.objects.filter(id__gt=product.id).order_by('id').first()

        if not next_product:
            next_product = Product.objects.order_by('id').first()

        if next_product:
            next_url = f"/store/curation/?id={next_product.id}"
        else:
            next_url = "/store/curation/"

        return JsonResponse({
            "success": True,
            "next_url": next_url
        })

    except Exception as e:
        print(f"❌ CURATION ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)
