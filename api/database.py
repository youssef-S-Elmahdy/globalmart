"""
Database connections
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from pymongo import MongoClient
import redis
from contextlib import contextmanager
import config

class Database:
    """Database connection manager"""

    def __init__(self):
        self.pg_conn = None
        self.mongo_client = None
        self.redis_client = None

    @contextmanager
    def get_postgres_connection(self):
        """Get PostgreSQL connection"""
        conn = None
        try:
            conn = psycopg2.connect(
                host=config.POSTGRES_HOST,
                port=config.POSTGRES_PORT,
                database=config.POSTGRES_DB,
                user=config.POSTGRES_USER,
                password=config.POSTGRES_PASSWORD,
                cursor_factory=RealDictCursor
            )
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()

    def get_mongodb_client(self):
        """Get MongoDB client"""
        if not self.mongo_client:
            self.mongo_client = MongoClient(
                host=config.MONGODB_HOST,
                port=config.MONGODB_PORT,
                username=config.MONGODB_USER,
                password=config.MONGODB_PASSWORD,
                authSource='admin'
            )
        return self.mongo_client[config.MONGODB_DB]

    def get_redis_client(self):
        """Get Redis client"""
        if not self.redis_client:
            self.redis_client = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                decode_responses=True
            )
        return self.redis_client

db = Database()
