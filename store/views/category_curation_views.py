"""Admin category curation — organizes products into curated sections on category pages."""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
import base64
from ..models import Category


# ════════════════════════════════════════════════════════════════
# CATEGORY CURATION & IMAGE MANAGEMENT
# ════════════════════════════════════════════════════════════════
def category_curation_workspace(request):
    """Display category curation workspace - ALLOW EDITING ANYTIME."""
    current_id = request.GET.get('id')

    if current_id:
        try:
            category = Category.objects.get(id=current_id)
        except Category.DoesNotExist:
            category = None
    else:
        category = Category.objects.order_by('id').first()

    prev_category = None
    next_category = None

    if category:
        prev_category = Category.objects.filter(id__lt=category.id).order_by('-id').first()
        next_category = Category.objects.filter(id__gt=category.id).order_by('id').first()

    total = Category.objects.count()
    current_position = 0
    if category:
        current_position = Category.objects.filter(id__lte=category.id).count()

    context = {
        'category': category,
        'prev_category': prev_category,
        'next_category': next_category,
        'total': total,
        'current_position': current_position,
    }

    print(f"\n✅ Category Curation - Category {category.id if category else 'None'}")
    print(f"   Position: {current_position}/{total}")

    return render(request, 'store/curation_category.html', context)


# ==============================================================================
# SECTION: Update Category Asset
# ==============================================================================

@csrf_exempt
def update_category_asset(request):
    """Handle category image upload - ALLOW EDITING ANYTIME."""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)

    try:
        category_id = request.POST.get('id')
        image_data = request.POST.get('image')

        if not category_id or not image_data:
            return JsonResponse({"success": False, "error": "Missing category ID or image data"}, status=400)

        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return JsonResponse({"success": False, "error": "Category not found"}, status=404)

        if not image_data.startswith('data:image'):
            return JsonResponse({"success": False, "error": "Invalid image format"}, status=400)

        format_part, imgstr = image_data.split(';base64,')
        ext = format_part.split('/')[-1].lower()

        if ext not in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
            return JsonResponse({"success": False, "error": f"Unsupported format: {ext}"}, status=400)

        raw_binary_file = ContentFile(base64.b64decode(imgstr))
        file_name = f"curated_cat_{category.id}.{ext}"
        category.image.save(file_name, raw_binary_file, save=True)
        print(f"✅ Updated category image: {file_name}")

        next_category = Category.objects.filter(id__gt=category.id).order_by('id').first()
        
        if not next_category:
            next_category = Category.objects.order_by('id').first()

        if next_category:
            next_url = f"/store/curation/category/?id={next_category.id}"
        else:
            next_url = "/store/curation/category/"

        return JsonResponse({"success": True, "next_url": next_url})

    except Exception as e:
        print(f"❌ CATEGORY CURATION ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"success": False, "error": str(e)}, status=500)
