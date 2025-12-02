"""
Test data generator and Kafka producer
"""

from producer import GlobalMartProducer
import logging

logging.basicConfig(level=logging.INFO)

def test_connection():
    """Test Kafka connection"""
    print("Testing Kafka connection...")
    producer = GlobalMartProducer()
    if producer.connect():
        print("✓ Connection successful")
        producer.close()
        return True
    else:
        print("✗ Connection failed")
        return False

def test_event_generation():
    """Test event generation"""
    print("\nTesting event generation...")
    producer = GlobalMartProducer()
    producer.generator.generate_user_pool(100)
    producer.generator.generate_product_catalog(100)

    # Generate sample events
    transaction = producer.generator.generate_transaction_event()
    product_view = producer.generator.generate_product_view_event()
    cart_event = producer.generator.generate_cart_event()

    print("✓ Transaction event:", transaction)
    print("✓ Product view event:", product_view)
    print("✓ Cart event:", cart_event)

def test_producer_run():
    """Test producer for 30 seconds"""
    print("\nTesting producer (30 seconds)...")
    producer = GlobalMartProducer()
    if producer.connect():
        producer.start_streaming(duration_seconds=30)
        print("✓ Producer test completed")
    else:
        print("✗ Producer test failed")

if __name__ == '__main__':
    test_connection()
    test_event_generation()
    test_producer_run()