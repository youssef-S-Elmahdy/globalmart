"""
Configuration for GlobalMart Data Generator
"""

import os

# Business Configuration
NUM_USERS = 10_000_000  # 10 million active users
NUM_PRODUCTS = 250_000  # 250k products
NUM_CATEGORIES = 100    # 100 categories
COUNTRIES = ['USA', 'UK', 'Canada', 'Germany', 'France']
DAILY_TRANSACTIONS = 100_000

# Event Generation Rates (events per second)
TARGET_THROUGHPUT = 500  # Total events per second
TRANSACTION_RATE = 100   # ~20% of throughput
PRODUCT_VIEW_RATE = 300  # ~60% of throughput
CART_EVENT_RATE = 100    # ~20% of throughput

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
    'Electronics', 'Clothing', 'Home & Garden', 'Books', 'Sports',
    'Toys', 'Food & Beverages', 'Beauty', 'Automotive', 'Health',
    # ... add 90 more categories
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