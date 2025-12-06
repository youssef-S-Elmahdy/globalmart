# Grafana Dashboard Update Instructions

## Status
✅ **Metrics Collection Infrastructure Complete:**
- kafka_metrics table: Created & Populated
- system_health_metrics table: Created & Populated
- Metrics collector: Running in background (PID 2152980)
- Data collecting every 10 seconds

## Quick Access to Grafana
- URL: http://localhost:3000
- Default credentials: admin/admin (or as configured)

## 3-Page Dashboard Structure

### Page 1: Data Ingestion (Part 1)
**Kafka Topic Metrics - Proving 500+ events/sec throughput**

SQL Queries for panels:
```sql
-- Panel 1: Total Events Ingested (Last Hour)
SELECT SUM(event_count) as total
FROM kafka_metrics
WHERE timestamp > NOW() - INTERVAL '1 hour';

-- Panel 2: Current Ingestion Rate (Gauge - Target: 500/sec)
SELECT COALESCE(SUM(event_count), 0) / 60.0 as rate
FROM kafka_metrics
WHERE timestamp > NOW() - INTERVAL '1 minute';

-- Panel 3: Events by Topic (Time Series)
SELECT
    timestamp,
    topic,
    event_count
FROM kafka_metrics
WHERE timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp;

-- Panel 4: Throughput Trend
SELECT
    timestamp,
    SUM(event_count) as total_events
FROM kafka_metrics
WHERE timestamp > NOW() - INTERVAL '6 hours'
GROUP BY timestamp
ORDER BY timestamp;
```

### Page 2: Stream Processing (Part 2) - EXISTING + ENHANCEMENTS
**Keep existing panels, add:**

```sql
-- Panel 5: Cart Abandonment (24h)
SELECT COUNT(*) as abandoned_carts
FROM cart_abandonment
WHERE abandonment_time > NOW() - INTERVAL '24 hours';

-- Panel 6: Low Stock Products Table
SELECT
    product_id,
    product_name,
    category,
    available_stock
FROM inventory_status
WHERE available_stock < 20
ORDER BY available_stock ASC
LIMIT 10;

-- Panel 7: Inventory Status Summary
SELECT
    COUNT(*) as total_products,
    COUNT(CASE WHEN available_stock < 10 THEN 1 END) as critical_stock,
    COUNT(CASE WHEN available_stock BETWEEN 10 AND 50 THEN 1 END) as low_stock
FROM inventory_status;
```

### Page 3: System Health (Part 5)
**Infrastructure Monitoring**

```sql
-- Panel 8: CPU Usage (Gauge)
SELECT metric_value as cpu_percent
FROM system_health_metrics
WHERE metric_name = 'cpu_usage'
ORDER BY timestamp DESC
LIMIT 1;

-- Panel 9: Memory Usage (Gauge)
SELECT metric_value as memory_percent
FROM system_health_metrics
WHERE metric_name = 'memory_usage'
ORDER BY timestamp DESC
LIMIT 1;

-- Panel 10: Disk Usage (Gauge)
SELECT metric_value as disk_percent
FROM system_health_metrics
WHERE metric_name = 'disk_usage'
ORDER BY timestamp DESC
LIMIT 1;

-- Panel 11: System Resources Over Time
SELECT
    timestamp,
    metric_name,
    metric_value
FROM system_health_metrics
WHERE metric_type = 'gauge'
    AND timestamp > NOW() - INTERVAL '6 hours'
ORDER BY timestamp;

-- Panel 12: Container Status
SELECT DISTINCT ON (metadata)
    metadata as container_name,
    CASE
        WHEN metric_value = 1 THEN 'UP ✓'
        ELSE 'DOWN ✗'
    END as status,
    timestamp as last_check
FROM system_health_metrics
WHERE metric_name = 'container_status'
ORDER BY metadata, timestamp DESC;
```

## Implementation Steps

### Recommended: Use Grafana UI
1. Open http://localhost:3000
2. Go to "GlobalMart Overview" dashboard
3. Click "Dashboard settings" → Edit
4. Add 3 collapsible rows:
   - Row 1: "📊 Data Ingestion" (Kafka Metrics)
   - Row 2: "⚡ Stream Processing" (Business Metrics)
   - Row 3: "🖥️  System Health" (Infrastructure)
5. Add panels using "Add Panel" button
6. Select visualization type (Stat, Gauge, Time Series, Table)
7. Paste SQL queries above
8. Configure panel titles and thresholds
9. Save dashboard

### Key Metrics to Highlight
- **Ingestion Rate:** Should show 500+ events/sec ✓
- **CPU/Memory:** Should be stable under 80%
- **Containers:** All globalmart-* containers UP
- **Low Stock:** Real-time inventory alerts

## Testing Commands

```bash
# Check metrics collector is running
ps aux | grep metrics_collector

# View collector logs
tail -f /tmp/metrics_collector.log

# Check data is being collected
psql -h localhost -U globalmart -d globalmart -c "SELECT COUNT(*) FROM kafka_metrics;"
psql -h localhost -U globalmart -d globalmart -c "SELECT COUNT(*) FROM system_health_metrics;"

# View latest metrics
psql -h localhost -U globalmart -d globalmart -c "
SELECT metric_name, metric_value, timestamp
FROM system_health_metrics
WHERE metric_type = 'gauge'
ORDER BY timestamp DESC
LIMIT 10;
"
```

## Deliverables Checklist
- [x] Database tables created (kafka_metrics, system_health_metrics)
- [x] Metrics collector script created
- [x] Metrics collector running in background
- [x] Data being collected every 10 seconds
- [ ] Grafana dashboard updated with 3 pages (manual UI step)
- [ ] All panels configured and displaying data

## Points Achieved
- Part 1 (Data Generation): Monitoring dashboard +2 points
- Part 5 (Infrastructure): System health monitoring +3 points
- **Total: ~5 additional points** toward 100/100 goal