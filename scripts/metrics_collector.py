#!/usr/bin/env python3
"""
Unified metrics collector for Grafana dashboard
Collects Kafka, Docker, and system metrics
"""

import psycopg2
import subprocess
import time
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import psutil
except ImportError:
    print("Installing psutil...")
    subprocess.run([sys.executable, "-m", "pip", "install", "psutil"], check=True)
    import psutil

try:
    from kafka import KafkaConsumer, TopicPartition
except ImportError:
    print("kafka-python not found, skipping Kafka metrics")
    KafkaConsumer = None
    TopicPartition = None

# Collection interval (seconds) - shorter interval tracks rate more closely
COLLECTION_INTERVAL = int(os.getenv("METRICS_INTERVAL", "5"))

# Track previous offsets to compute deltas/rates
prev_offsets = {}

# PostgreSQL connection
def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='globalmart',
        user='globalmart',
        password='globalmart123'
    )

def collect_kafka_metrics():
    """Collect Kafka topic metrics using end offsets to compute deltas."""
    if KafkaConsumer is None or TopicPartition is None:
        return []

    topics = ['transactions', 'product_views', 'cart_events']
    metrics = []

    try:
        consumer = KafkaConsumer(
            bootstrap_servers='localhost:9093',
            enable_auto_commit=False,
            consumer_timeout_ms=2000
        )

        for topic in topics:
            try:
                partitions = consumer.partitions_for_topic(topic) or []
                if not partitions:
                    continue

                tps = [TopicPartition(topic, p) for p in partitions]
                end_offsets = consumer.end_offsets(tps)
                total = sum(end_offsets.values())

                prev_total = prev_offsets.get(topic, total)
                delta = max(total - prev_total, 0)
                rate = delta / COLLECTION_INTERVAL if COLLECTION_INTERVAL > 0 else 0

                prev_offsets[topic] = total

                metrics.append({
                    'topic': topic,
                    'count': delta,
                    'rate': rate
                })
            except Exception as e:
                print(f"Error collecting metrics for topic {topic}: {e}")

        consumer.close()
    except Exception as e:
        print(f"Error connecting to Kafka: {e}")

    return metrics

def collect_docker_metrics():
    """Collect Docker container status using sudo"""
    try:
        result = subprocess.run(
            ['sudo', 'docker', 'ps', '--format', '{{.Names}}\t{{.Status}}'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            # Try without sudo
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}\t{{.Status}}'],
                capture_output=True,
                text=True,
                timeout=5
            )

        containers = []
        for line in result.stdout.strip().split('\n'):
            if '\t' in line:
                name, status = line.split('\t', 1)
                if 'globalmart' in name.lower():
                    containers.append({'name': name, 'status': status})

        return containers
    except Exception as e:
        print(f"Error collecting Docker metrics: {e}")
        return []

def collect_system_metrics():
    """Collect system resource metrics using psutil"""
    try:
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }
    except Exception as e:
        print(f"Error collecting system metrics: {e}")
        return {
            'cpu_percent': 0,
            'memory_percent': 0,
            'disk_percent': 0
        }

def write_metrics():
    """Write all metrics to PostgreSQL"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Kafka metrics
        kafka_data = collect_kafka_metrics()
        for metric in kafka_data:
            cur.execute("""
                INSERT INTO kafka_metrics (topic, event_count, rate, timestamp)
                VALUES (%s, %s, %s, NOW())
            """, (metric['topic'], metric['count'], metric['rate']))

        # System metrics
        system = collect_system_metrics()
        cur.execute("""
            INSERT INTO system_health_metrics
            (metric_name, metric_value, metric_type, timestamp)
            VALUES
            ('cpu_usage', %s, 'gauge', NOW()),
            ('memory_usage', %s, 'gauge', NOW()),
            ('disk_usage', %s, 'gauge', NOW())
        """, (system['cpu_percent'], system['memory_percent'], system['disk_percent']))

        # Docker container status
        containers = collect_docker_metrics()
        for container in containers:
            status_value = 1 if 'Up' in container['status'] else 0
            cur.execute("""
                INSERT INTO system_health_metrics
                (metric_name, metric_value, metric_type, timestamp, metadata)
                VALUES ('container_status', %s, 'status', NOW(), %s)
            """, (status_value, container['name']))

        conn.commit()

        # Log summary
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Metrics collected:")
        print(f"  - Kafka topics: {len(kafka_data)} (event deltas per {COLLECTION_INTERVAL}s)")
        print(f"  - System: CPU={system['cpu_percent']:.1f}%, MEM={system['memory_percent']:.1f}%, DISK={system['disk_percent']:.1f}%")
        print(f"  - Containers: {len(containers)}")

    except Exception as e:
        print(f"Error writing metrics: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    print("=" * 70)
    print("GlobalMart Metrics Collector")
    print("=" * 70)
    print("Collecting metrics every 10 seconds...")
    print("Press Ctrl+C to stop")
    print("=" * 70)

    while True:
        try:
            write_metrics()
            time.sleep(10)  # Collect every 10 seconds
        except KeyboardInterrupt:
            print("\n\nStopping metrics collector...")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(10)
