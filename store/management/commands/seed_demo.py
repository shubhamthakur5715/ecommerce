from django.core.management.base import BaseCommand
from store.models import Category, Supplier, Product

class Command(BaseCommand):
    help = "Create demo categories, supplier and products."

    def handle(self, *args, **kwargs):
        supplier, _ = Supplier.objects.get_or_create(name="Demo Supplier", defaults={"email": "supplier@example.com"})
        data = [
            ("Tech", "Wireless Headphones", "Comfortable wireless headphones with clear sound.", 1499, 850, True),
            ("Home", "LED Desk Lamp", "Minimal desk lamp for study and work.", 799, 420, True),
            ("Lifestyle", "Insulated Water Bottle", "Reusable insulated bottle for daily use.", 499, 220, False),
            ("Tech", "Bluetooth Speaker", "Compact speaker for travel and home.", 1199, 680, False),
        ]
        for cat_name, name, desc, price, cost, featured in data:
            category, _ = Category.objects.get_or_create(name=cat_name)
            Product.objects.get_or_create(name=name, defaults={
                "category": category, "supplier": supplier, "description": desc,
                "selling_price": price, "supplier_cost": cost, "stock_quantity": 50,
                "featured": featured, "active": True,
                "image_url": "https://placehold.co/800x600?text=" + name.replace(" ", "+")
            })
        self.stdout.write(self.style.SUCCESS("Demo data ready."))
