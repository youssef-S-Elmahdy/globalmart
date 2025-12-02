from datetime import datetime
import uuid

# User Profile Schema
USER_SCHEMA = {
    "user_id": "string (UUID)",
    "email": "string",
    "age": "integer (18-80)",
    "country": "string (USA, UK, Canada, Germany, France)",
    "registration_date": "timestamp",
    "preferences": ["array of categories"]
}

# Transaction Event Schema
TRANSACTION_SCHEMA = {
    "transaction_id": "string (UUID)",
    "user_id": "string (UUID)",
    "timestamp": "timestamp (ISO 8601)",
    "products": [{
        "product_id": "string (UUID)",
        "quantity": "integer (1-10)",
        "price": "float (10.00-2000.00)"
    }],
    "total_amount": "float",
    "payment_method": "string (credit_card, paypal, debit_card, apple_pay)"
}

# Product View Event Schema
PRODUCT_VIEW_SCHEMA = {
    "event_id": "string (UUID)",
    "user_id": "string (UUID)",
    "product_id": "string (UUID)",
    "timestamp": "timestamp",
    "session_id": "string (UUID)",
    "duration_seconds": "integer (5-300)"
}

# Cart Event Schema
CART_EVENT_SCHEMA = {
    "event_id": "string (UUID)",
    "user_id": "string (UUID)",
    "product_id": "string (UUID)",
    "timestamp": "timestamp",
    "action": "string (add, remove, update)",
    "quantity": "integer (0-10)",
    "session_id": "string (UUID)"
}

# Product Catalog Schema
PRODUCT_SCHEMA = {
    "product_id": "string (UUID)",
    "name": "string",
    "category": "string (100 categories)",
    "price": "float (10.00-2000.00)",
    "inventory": "integer (0-1000)",
    "ratings": "float (1.0-5.0)"
}