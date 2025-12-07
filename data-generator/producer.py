"""
Kafka Producer for GlobalMart events - Optimized for 500 events/second
"""

from kafka import KafkaProducer
import json
import time
import logging
from datetime import datetime
from generators import DataGenerator
from concurrent.futures import ThreadPoolExecutor
import threading
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
        self.stats_lock = threading.Lock()
        self.start_time = None

    def connect(self):
        """Connect to Kafka with optimized settings for high throughput"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.config.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks=1,  # Only wait for leader acknowledgment (faster)
                retries=3,
                max_in_flight_requests_per_connection=32,  # Increased for better batching
                batch_size=32768,  # 32KB batches for efficiency
                linger_ms=5,  # Wait 5ms to form batches
                compression_type='snappy'  # Compress for reduced network I/O
            )
            logger.info("Connected to Kafka successfully with optimized settings")
            logger.info("  - Batch size: 32KB")
            logger.info("  - Compression: snappy")
            logger.info("  - Max in-flight requests: 32")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            return False

    def send_event_async(self, topic, event, event_type):
        """Send event asynchronously with callback (non-blocking)"""
        def on_success(metadata):
            with self.stats_lock:
                self.stats[event_type] += 1

        def on_error(exc):
            logger.error(f"Error sending to {topic}: {exc}")
            with self.stats_lock:
                self.stats['errors'] += 1

        # Fire and forget with callbacks - returns immediately!
        self.producer.send(topic, value=event) \
            .add_callback(on_success) \
            .add_errback(on_error)

    def generate_batch(self, event_type, count):
        """Generate a batch of events in parallel"""
        topic = self.config.KAFKA_TOPICS[event_type]

        if event_type == 'transactions':
            for _ in range(count):
                event = self.generator.generate_transaction_event()
                self.send_event_async(topic, event, event_type)
        elif event_type == 'product_views':
            for _ in range(count):
                event = self.generator.generate_product_view_event()
                self.send_event_async(topic, event, event_type)
        elif event_type == 'cart_events':
            for _ in range(count):
                event = self.generator.generate_cart_event()
                self.send_event_async(topic, event, event_type)

    def start_streaming(self, duration_seconds=None):
        """Start streaming events with thread pool for parallel generation"""
        logger.info("Starting event generation with threading...")
        logger.info(f"Target throughput: {self.config.TARGET_THROUGHPUT} events/second")

        # Generate initial data at configured scale
        logger.info("Generating user pool and product catalog...")
        self.generator.generate_user_pool(self.config.NUM_USERS)
        self.generator.generate_product_catalog(self.config.NUM_PRODUCTS)
        logger.info("Initial data generation complete")

        self.start_time = time.time()
        iteration = 0

        try:
            # Use thread pool for parallel event generation
            with ThreadPoolExecutor(max_workers=10) as executor:
                while True:
                    iteration += 1
                    cycle_start = time.time()

                    # Submit all event generation tasks in parallel
                    futures = [
                        executor.submit(self.generate_batch, 'transactions', self.config.TRANSACTION_RATE),
                        executor.submit(self.generate_batch, 'product_views', self.config.PRODUCT_VIEW_RATE),
                        executor.submit(self.generate_batch, 'cart_events', self.config.CART_EVENT_RATE)
                    ]

                    # Wait for all batches to be submitted (not sent - that's async)
                    for future in futures:
                        future.result()

                    # Flush producer to ensure messages are sent
                    self.producer.flush()

                    # Log statistics every 10 seconds
                    if iteration % 10 == 0:
                        elapsed = time.time() - self.start_time
                        with self.stats_lock:
                            total = self.stats['transactions'] + self.stats['product_views'] + self.stats['cart_events']
                            rate = total / elapsed if elapsed > 0 else 0

                            logger.info(f"""
    === Statistics (t={int(elapsed)}s, rate={rate:.1f}/s) ===
    Transactions:  {self.stats['transactions']:>6} ({self.stats['transactions']/elapsed:.1f}/s)
    Product Views: {self.stats['product_views']:>6} ({self.stats['product_views']/elapsed:.1f}/s)
    Cart Events:   {self.stats['cart_events']:>6} ({self.stats['cart_events']/elapsed:.1f}/s)
    Errors:        {self.stats['errors']:>6}
    Total Events:  {total:>6} ({rate:.1f}/s)
    Target:        500.0/s {'✓ ACHIEVED' if rate >= 500 else '✗ BELOW TARGET'}
                            """)

                    # Check if duration limit reached
                    if duration_seconds and (time.time() - self.start_time) >= duration_seconds:
                        logger.info(f"Reached duration limit of {duration_seconds} seconds")
                        break

                    # Sleep to maintain 1-second cycle
                    cycle_duration = time.time() - cycle_start
                    sleep_time = max(0, 1.0 - cycle_duration)
                    if sleep_time > 0:
                        time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("\nStopping event generation...")
        finally:
            self.close()
            self.print_final_stats()

    def print_final_stats(self):
        """Print final statistics"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            with self.stats_lock:
                total = self.stats['transactions'] + self.stats['product_views'] + self.stats['cart_events']
                rate = total / elapsed if elapsed > 0 else 0

                logger.info(f"""
=====================================
FINAL STATISTICS
=====================================
Duration:        {elapsed:.1f} seconds
Total Events:    {total:,}
Average Rate:    {rate:.1f} events/second
Target Rate:     500.0 events/second
Status:          {'✓ SUCCESS' if rate >= 500 else '✗ FAILED'}

Breakdown:
  Transactions:  {self.stats['transactions']:,} ({self.stats['transactions']/elapsed:.1f}/s)
  Product Views: {self.stats['product_views']:,} ({self.stats['product_views']/elapsed:.1f}/s)
  Cart Events:   {self.stats['cart_events']:,} ({self.stats['cart_events']/elapsed:.1f}/s)
  Errors:        {self.stats['errors']:,}
=====================================
                """)

    def close(self):
        """Close producer connection"""
        if self.producer:
            logger.info("Flushing remaining messages...")
            self.producer.flush()
            self.producer.close()
            logger.info("Producer closed")

if __name__ == '__main__':
    producer = GlobalMartProducer()
    if producer.connect():
        producer.start_streaming()
