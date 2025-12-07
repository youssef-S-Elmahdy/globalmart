"""
Configuration for GlobalMart Data Generator
"""

import os

# Business Configuration aligned to scenario
NUM_USERS = 100_000         # subset for faster startup (scenario: 10M)
NUM_PRODUCTS = 250_000      # 250k products
NUM_CATEGORIES = 100        # 100 categories
COUNTRIES = ['USA', 'UK', 'Canada', 'Germany', 'France']
DAILY_TRANSACTIONS = 100_000

# Event Generation Rates (events per second)
# Target 500 events/sec overall, with transactions sized to ~100k/day (~1-2 tx/sec)
TARGET_THROUGHPUT = 600
TRANSACTION_RATE = 200        # ~17200k/day, won't bu running for a day
PRODUCT_VIEW_RATE = 300     # balance of the 500/sec target
CART_EVENT_RATE = 100       # balance of the 500/sec target

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'globalmart-kafka:9092')
KAFKA_TOPICS = {
    'transactions': 'transactions',
    'product_views': 'product_views',
    'cart_events': 'cart_events',
    'system_metrics': 'system_metrics'
}

# Data Generation Parameters
PRODUCT_CATEGORIES = [
    'Electronics', 'Smartphones', 'Computers', 'Tablets', 'Wearables',
    'TV & Home Theater', 'Cameras', 'Audio & Headphones', 'Gaming',
    'Networking', 'Office Electronics', 'Software', 'Books', 'E-books',
    'Movies & TV', 'Music', 'Video Games', 'Toys', 'Board Games',
    'Puzzles', 'Outdoor Toys', 'STEM Kits', 'Clothing', 'Shoes',
    'Accessories', 'Jewelry', 'Watches', 'Handbags', 'Luggage',
    'Sports', 'Fitness', 'Cycling', 'Camping & Hiking', 'Fishing',
    'Golf', 'Tennis', 'Team Sports', 'Water Sports', 'Winter Sports',
    'Home & Garden', 'Furniture', 'Home Decor', 'Lighting',
    'Kitchen & Dining', 'Appliances', 'Bedding & Bath', 'Storage',
    'Cleaning Supplies', 'Tools & Hardware', 'Lawn & Garden',
    'Patio & Outdoor', 'Grills & Outdoor Cooking', 'Automotive',
    'Car Electronics', 'Car Care', 'Auto Parts', 'Motorcycle',
    'Beauty', 'Skincare', 'Hair Care', 'Makeup', 'Fragrance',
    'Personal Care', 'Health', 'Vitamins & Supplements',
    'Medical Supplies', 'Baby', 'Diapering', 'Baby Gear', 'Nursery',
    'Feeding', 'Toys for Baby', 'Pet Supplies', 'Dog', 'Cat',
    'Small Animal', 'Aquatic', 'Bird', 'Food & Beverages', 'Gourmet',
    'Snacks', 'Beverages', 'Coffee & Tea', 'Pantry Staples',
    'Specialty Diet', 'Crafts & Sewing', 'Art Supplies',
    'Musical Instruments', 'Industrial & Scientific', 'Safety',
    'Lab Supplies', 'Office Supplies', 'School Supplies',
    'Party Supplies', 'Gifts', 'Collectibles', 'Antiques',
    'Real Estate', 'Services', 'Subscriptions', 'Digital Goods',
    'Travel'
]

PAYMENT_METHODS = ['credit_card', 'paypal', 'debit_card', 'apple_pay', 'google_pay']

# Price Ranges by Category (min, max)
PRICE_RANGES = {
    'Electronics': (50, 2000),
    'Clothing': (10, 200),
    'Home & Garden': (15, 500),
    'Books': (10, 50),
    'Sports': (20, 300),
    # Default for others
    'default': (10, 200)
}
