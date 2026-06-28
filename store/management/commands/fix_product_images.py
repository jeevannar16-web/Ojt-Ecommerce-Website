from django.core.management.base import BaseCommand
from django.conf import settings
from store.models import Product, Category
import json, os


class Command(BaseCommand):
    help = 'Restore product/category images from fixture if they are missing'

    def handle(self, *args, **options):
        fixture_path = os.path.join(settings.BASE_DIR, 'fixtures/seed_data.json')
        if not os.path.exists(fixture_path):
            self.stdout.write('Fixture not found, skipping')
            return

        with open(fixture_path) as f:
            data = json.load(f)

        product_images = {}
        cat_images = {}
        for entry in data:
            if entry['model'] == 'store.product':
                product_images[entry['pk']] = entry['fields'].get('image')
            elif entry['model'] == 'store.category':
                cat_images[entry['pk']] = entry['fields'].get('image')

        fixed = 0
        for pk, path in product_images.items():
            if path and Product.objects.filter(pk=pk, image__isnull=True).update(image=path):
                fixed += 1
        for pk, path in cat_images.items():
            if path and Category.objects.filter(pk=pk, image__isnull=True).update(image=path):
                fixed += 1

        if fixed:
            self.stdout.write(self.style.SUCCESS(f'Restored images for {fixed} products/categories'))
        else:
            count_null = Product.objects.filter(image__isnull=True).count() + Category.objects.filter(image__isnull=True).count()
            self.stdout.write(f'No images to restore ({count_null} still null)')
