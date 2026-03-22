import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Use get_user_model for custom user models
from django.contrib.auth import get_user_model 
from marketplace.models import Product

User = get_user_model()

def seed():
    # 1. Create a Sample Farmer
    farmer, created = User.objects.get_or_create(username='farmer_rahul')
    if created:
        farmer.set_password('hackathon2026')
        # If your custom user requires other fields (like is_farmer=True), add them here if it throws an error.
        farmer.save()

    # 2. Add Sample Crops
    crops = [
        {'name': 'Tomato', 'price': 25, 'qty': 500, 'loc': 'Jaipur'},
        {'name': 'Wheat', 'price': 22, 'qty': 2000, 'loc': 'Kota'},
        {'name': 'Watermelon', 'price': 15, 'qty': 800, 'loc': 'Tonk'},
        {'name': 'Onion', 'price': 40, 'qty': 300, 'loc': 'Alwar'},
        {'name': 'Potato', 'price': 18, 'qty': 1200, 'loc': 'Jaipur'},
    ]

    for c in crops:
        Product.objects.create(
            farmer=farmer,
            name=c['name'],
            price_per_unit=c['price'],
            quantity_available=c['qty'],
            location=c['loc'],
            harvest_date=timezone.now().date() - timedelta(days=2)
        )
    print("Database Seeded Successfully!")

if __name__ == '__main__':
    seed()