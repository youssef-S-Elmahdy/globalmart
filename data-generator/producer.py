"""
Kafka Producer for GlobalMart events
"""

from kafka import KafkaProducer
import json
import time
import logging
from datetime import datetime
from generators import DataGenerator
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GlobalMartProducer:
    def __init__(self):
        self.config = config
        self.producer = None
        self.generator = DataGenerator(config)
        self.stats = {
            'transactions': 0,
            'product_views': 0,
            'cart_events': 0,
            'errors': 0
        }

    def connect(self):
        """Connect to Kafka"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.config.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=5
            )
            logger.info("Connected to Kafka successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            return False

    def send_event(self, topic, event):
        """Send event to Kafka topic"""
        try:
            future = self.producer.send(topic, value=event)
            future.get(timeout=10)  # Wait for confirmation
            return True
        except Exception as e:
            logger.error(f"Error sending to {topic}: {e}")
            self.stats['errors'] += 1
            return False

    def start_streaming(self, duration_seconds=None):
        """Start streaming events"""
        logger.info("Starting event generation...")

        # Generate initial data
        self.generator.generate_user_pool(10000)  # Generate 10k users
        self.generator.generate_product_catalog(10000)  # Generate 10k products

        start_time = time.time()
        iteration = 0

        try:
            while True:
                iteration += 1
                cycle_start = time.time()

                # Generate events based on configured rates
                # Transaction events (100/sec)
                for _ in range(self.config.TRANSACTION_RATE):
                    event = self.generator.generate_transaction_event()
                    if self.send_event(self.config.KAFKA_TOPICS['transactions'], event):
                        self.stats['transactions'] += 1

                # Product view events (300/sec)
                for _ in range(self.config.PRODUCT_VIEW_RATE):
                    event = self.generator.generate_product_view_event()
                    if self.send_event(self.config.KAFKA_TOPICS['product_views'], event):
                        self.stats['product_views'] += 1

                # Cart events (100/sec)
                for _ in range(self.config.CART_EVENT_RATE):
                    event = self.generator.generate_cart_event()
                    if self.send_event(self.config.KAFKA_TOPICS['cart_events'], event):
                        self.stats['cart_events'] += 1

                # Log statistics every 10 seconds
                if iteration % 10 == 0:
                    elapsed = time.time() - start_time
                    logger.info(f"""
                    === Statistics (after {elapsed:.1f}s) ===
                    Transactions: {self.stats['transactions']} ({self.stats['transactions']/elapsed:.1f}/s)
                    Product Views: {self.stats['product_views']} ({self.stats['product_views']/elapsed:.1f}/s)
                    Cart Events: {self.stats['cart_events']} ({self.stats['cart_events']/elapsed:.1f}/s)
                    Errors: {self.stats['errors']}
                    Total Events: {sum([self.stats['transactions'], self.stats['product_views'], self.stats['cart_events']])}
                    """)

                # Check if duration limit reached
                if duration_seconds and (time.time() - start_time) >= duration_seconds:
                    logger.info(f"Reached duration limit of {duration_seconds} seconds")
                    break

                # Sleep to maintain target rate (1 second per cycle)
                cycle_duration = time.time() - cycle_start
                sleep_time = max(0, 1.0 - cycle_duration)
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("Stopping event generation...")
        finally:
            self.close()

    def close(self):
        """Close producer connection"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("Producer closed")

if __name__ == '__main__':
    producer = GlobalMartProducer()
    if producer.connect():
        producer.start_streaming()