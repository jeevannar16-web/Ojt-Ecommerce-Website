import os
import django

# STEP 1: Set up the Django configuration environment first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness_hub.settings')
django.setup()

# STEP 2: Import your models
from store.models import Product

def fallback_order_relink():
    print("🔄 Starting Sequential Product Image Re-linking Script...")
    
    media_products_dir = os.path.join('media', 'products')
    
    if not os.path.exists(media_products_dir):
        print(f"❌ Could not find product folder at: {media_products_dir}")
        return

    # Grab and sort all your product images alphabetically so they align cleanly
    prod_files = sorted([f for f in os.listdir(media_products_dir) if f.startswith('curated_prod_')])
    
    # Grab all your products from the database sorted by ID
    products = Product.objects.all().order_by('id')
    
    if not prod_files:
        print("❌ No images starting with 'curated_prod_' found in media/products/")
        return
        
    print(f"📸 Found {len(prod_files)} curated images on your disk.")
    print(f"📦 Found {products.count()} products inside your active database.")

    # Loop through them together in exact matching order
    linked_count = 0
    for index, product in enumerate(products):
        if index < len(prod_files):
            filename = prod_files[index]
            product.image = f"products/{filename}"
            product.save()
            print(f"✨ Linked row {index+1}: {product.name} (DB ID: {product.id}) -> products/{filename}")
            linked_count += 1
        else:
            print(f"⚠️ Ran out of images! Product '{product.name}' left blank.")

    print(f"\n🎉 Done! Successfully filled {linked_count} products with your curated images.")

if __name__ == "__main__":
    fallback_order_relink()