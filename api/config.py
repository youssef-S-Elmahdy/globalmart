"""
API Configuration
"""

import os

# API Settings
API_TITLE = "GlobalMart Analytics API"
API_VERSION = "1.0.0"
API_DESCRIPTION = """
GlobalMart Real-Time E-Commerce Analytics Platform API

## Features
* **Sales Metrics**: Query real-time and historical sales data
* **Customer Analytics**: Access customer segmentation and RFM analysis
* **Product Performance**: Retrieve product analytics and trends
* **Real-time Monitoring**: Get live transaction and inventory data

## Authentication
All endpoints require API key authentication.
"""

# Database Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "globalmart-postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_DB = os.getenv("POSTGRES_DB", "globalmart")
POSTGRES_USER = os.getenv("POSTGRES_USER", "globalmart")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "globalmart123")

MONGODB_HOST = os.getenv("MONGODB_HOST", "globalmart-mongodb")
MONGODB_PORT = int(os.getenv("MONGODB_PORT", 27017))
MONGODB_DB = os.getenv("MONGODB_DB", "globalmart_dw")
MONGODB_USER = os.getenv("MONGODB_USER", "globalmart")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD", "globalmart123")

# Redis Configuration (for caching)
REDIS_HOST = os.getenv("REDIS_HOST", "globalmart-redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# API Security
SECRET_KEY = "your-secret-key-change-this-in-production"
API_KEY = "globalmart-api-key-2024"

# CORS Settings
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:8083",
    "http://localhost:3001"
]
