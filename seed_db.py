# seed_db.py
import os, django
from django.db import transaction
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql_crm.settings')
django.setup()
from crm.models import Customer, Product, Order
@transaction.atomic
def seed_database():
    print("Seeding database...")
    customers_data = [{'name': 'Alice', 'email': 'alice@example.com', 'phone': '555-123-4567'}, {'name': 'Bob', 'email': 'bob@example.com'}, {'name': 'Carol', 'email': 'carol@example.com'}]
    for data in customers_data:
        Customer.objects.get_or_create(email=data['email'], defaults=data)
    products_data = [{'name': 'Laptop', 'price': 999.99, 'stock': 50}, {'name': 'Mouse', 'price': 25.50, 'stock': 200}, {'name': 'Keyboard', 'price': 75.00, 'stock': 150}]
    for data in products_data:
        Product.objects.get_or_create(name=data['name'], defaults=data)
    print("Database seeded successfully!")
if __name__ == '__main__':
    seed_database()
