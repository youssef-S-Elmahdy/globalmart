"""
Data generators for GlobalMart events
"""

from faker import Faker
import random
import uuid
from datetime import datetime, timedelta
import json

fake = Faker()

class DataGenerator:
    def __init__(self, config):
        self.config = config
        self.users = []
        self.products = []
        self.active_sessions = {}

    def generate_user_pool(self, num_users=10000):
        """Generate a pool of users for realistic data"""
        print(f"Generating {num_users} users...")
        self.users = []
        for _ in range(num_users):
            user = {
                'user_id': str(uuid.uuid4()),
                'email': fake.email(),
                'age': random.randint(18, 80),
                'country': random.choice(self.config.COUNTRIES),
                'registration_date': fake.date_time_between(
                    start_date='-2y',
                    end_date='now'
                ).isoformat(),
                'preferences': random.sample(
                    self.config.PRODUCT_CATEGORIES,
                    k=random.randint(1, 5)
                )
            }
            self.users.append(user)
        print(f"Generated {len(self.users)} users")
        return self.users

    def generate_product_catalog(self, num_products=10000):
        """Generate product catalog"""
        print(f"Generating {num_products} products...")
        self.products = []
        for _ in range(num_products):
            category = random.choice(self.config.PRODUCT_CATEGORIES)
            price_range = self.config.PRICE_RANGES.get(
                category,
                self.config.PRICE_RANGES['default']
            )

            product = {
                'product_id': str(uuid.uuid4()),
                'name': fake.catch_phrase(),
                'category': category,
                'price': round(random.uniform(*price_range), 2),
                'inventory': random.randint(0, 1000),
                'ratings': round(random.uniform(1.0, 5.0), 1)
            }
            self.products.append(product)
        print(f"Generated {len(self.products)} products")
        return self.products

    def generate_transaction_event(self):
        """Generate a transaction event"""
        user = random.choice(self.users)
        num_items = random.randint(1, 5)
        products = random.sample(self.products, num_items)

        transaction_products = []
        total_amount = 0

        for product in products:
            quantity = random.randint(1, 3)
            item_total = product['price'] * quantity
            total_amount += item_total

            transaction_products.append({
                'product_id': product['product_id'],
                'quantity': quantity,
                'price': product['price']
            })

        event = {
            'transaction_id': str(uuid.uuid4()),
            'user_id': user['user_id'],
            'timestamp': datetime.utcnow().isoformat(),
            'products': transaction_products,
            'total_amount': round(total_amount, 2),
            'payment_method': random.choice(self.config.PAYMENT_METHODS),
            'country': user['country']
        }

        return event

    def generate_product_view_event(self):
        """Generate a product view event"""
        user = random.choice(self.users)
        product = random.choice(self.products)

        # Create or get session ID
        if user['user_id'] not in self.active_sessions or \
           random.random() < 0.1:  # 10% chance of new session
            self.active_sessions[user['user_id']] = str(uuid.uuid4())

        event = {
            'event_id': str(uuid.uuid4()),
            'user_id': user['user_id'],
            'product_id': product['product_id'],
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': self.active_sessions[user['user_id']],
            'duration_seconds': random.randint(5, 300),
            'category': product['category']
        }

        return event

    def generate_cart_event(self):
        """Generate a cart event (add/remove/update)"""
        user = random.choice(self.users)
        product = random.choice(self.products)
        action = random.choice(['add', 'add', 'add', 'remove', 'update'])

        # Create or get session ID
        if user['user_id'] not in self.active_sessions:
            self.active_sessions[user['user_id']] = str(uuid.uuid4())

        event = {
            'event_id': str(uuid.uuid4()),
            'user_id': user['user_id'],
            'product_id': product['product_id'],
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'quantity': random.randint(1, 5) if action != 'remove' else 0,
            'session_id': self.active_sessions[user['user_id']]
        }

        return event