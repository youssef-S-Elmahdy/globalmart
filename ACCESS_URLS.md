# GlobalMart Platform - Access URLs

**Last Updated:** December 6, 2025

---

## 🌐 Web Interfaces

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3001 | admin / admin123 |
| **Web Explorer** | http://localhost:8000/explorer | None |
| **API Documentation** | http://localhost:8000/docs | None |
| **Streamlit Dashboard** | http://localhost:8501 | None |
| **Spark Master UI** | http://localhost:8080 | None |
| **MongoDB Express** | http://localhost:8081 | admin / pass |
| **Kafka UI** | http://localhost:8082 | None |

---

## 📊 API Endpoints

**Base URL:** http://localhost:8000

### Health Check
- `GET /health` - API health status

### Sales Metrics
- `GET /sales/metrics` - Get sales metrics
- `GET /sales/trends` - Get sales trends

### Inventory
- `GET /inventory/status` - Current inventory status
- `GET /inventory/low-stock` - Low stock items

### Anomalies
- `GET /anomalies/transactions` - Transaction anomalies
- `GET /anomalies/recent` - Recent anomalies

### Cart Abandonment
- `GET /carts/abandoned` - Abandoned cart sessions
- `GET /carts/analytics` - Cart abandonment analytics

### MongoDB Data Warehouse
- `GET /warehouse/customers` - Customer segments (RFM)
- `GET /warehouse/products` - Product performance
- `GET /warehouse/sales` - Sales analytics

### Custom Queries
- `POST /api/query` - Execute custom SQL query (SELECT only)

---

## 🗄️ Database Connections

### PostgreSQL (Real-time Metrics)
```bash
Host: localhost
Port: 5432
Database: globalmart
Username: globalmart
Password: globalmart123
```

**Connection String:**
```
postgresql://globalmart:globalmart123@localhost:5432/globalmart
```

**Docker Access:**
```bash
sudo docker exec -it globalmart-postgres psql -U globalmart -d globalmart
```

### MongoDB (Data Warehouse)
```bash
Host: localhost
Port: 27017
Database: globalmart_dw
Username: globalmart
Password: globalmart123
```

**Connection String:**
```
mongodb://globalmart:globalmart123@localhost:27017/globalmart_dw
```

**Docker Access:**
```bash
sudo docker exec -it globalmart-mongodb mongosh -u globalmart -p globalmart123 globalmart_dw
```

### Redis (Cache)
```bash
Host: localhost
Port: 6379
```

**Docker Access:**
```bash
sudo docker exec -it globalmart-redis redis-cli
```

---

## 🔧 Management URLs

### Kafka
- **Bootstrap Server:** localhost:9092
- **Zookeeper:** localhost:2181
- **Kafka UI:** http://localhost:8082

**Topics:**
- `transactions`
- `product_views`
- `cart_events`

**Check Topics:**
```bash
sudo docker exec globalmart-kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Spark Cluster
- **Master URL:** spark://localhost:7077
- **Web UI:** http://localhost:8080
- **Worker 1 UI:** http://localhost:8081
- **Worker 2 UI:** http://localhost:8082

---

## 🚀 Quick Access Commands

### Open Web Explorer
```bash
xdg-open http://localhost:8000/explorer
# or
firefox http://localhost:8000/explorer
```

### Open Grafana
```bash
xdg-open http://localhost:3001
# or
firefox http://localhost:3001
```

### Check API Health
```bash
curl http://localhost:8000/health
```

### Get Recent Sales Metrics
```bash
curl http://localhost:8000/sales/metrics | jq
```

### Get Low Stock Items
```bash
curl http://localhost:8000/inventory/low-stock | jq
```

---

## 📝 Important Notes

1. **Grafana Port:** Changed from 3000 to **3001** (configured in docker-compose.api.yml)
2. **Grafana Password:** Changed from default `admin` to `admin123`
3. **All APIs:** Support CORS for frontend access
4. **Web Explorer:** Located at `/explorer`, not root
5. **API Docs:** Interactive Swagger UI at `/docs`

---

## 🔍 Verification

Run this to check all services:
```bash
/home/g7/Desktop/BigData/CHECK_STATUS.sh
```

Expected output:
```
✅ FastAPI:           http://localhost:8000/explorer
✅ Streamlit:         http://localhost:8501
✅ Grafana:           http://localhost:3001
✅ MongoDB Express:   http://localhost:8081
✅ Spark Master UI:   http://localhost:8080
```

---

**Created:** December 6, 2025
**Path:** /home/g7/Desktop/BigData/ACCESS_URLS.md
