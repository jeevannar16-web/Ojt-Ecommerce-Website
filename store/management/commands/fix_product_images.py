import os, json
from django.conf import settings
from django.core.management.base import BaseCommand
from store.models import Product, Category


class Command(BaseCommand):
    help = 'Sync product/category image paths from fixture (fixes extensions & sanitizes)'

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
            if path:
                fixed += Product.objects.filter(pk=pk).exclude(image=path).update(image=path)
        for pk, path in cat_images.items():
            if path:
                fixed += Category.objects.filter(pk=pk).exclude(image=path).update(image=path)

        if fixed:
            self.stdout.write(self.style.SUCCESS(
                f'Fixed image paths for {fixed} products/categories (extensions stripped, chars sanitized)'
            ))
        else:
            self.stdout.write('All image paths already match fixture')
