# GlobalMart Data Warehouse Schema

## Overview
The GlobalMart Data Warehouse uses a **Star Schema** design implemented in MongoDB with the following structure:

---

## Star Schema Architecture

```
        dim_time
            |
            |
fact_sales  +---+  dim_products
            |
            |
        dim_customers
```

---

## Fact Tables

### 1. **fact_sales**
Primary fact table containing aggregated sales transactions.

| Field | Type | Description |
|-------|------|-------------|
| date_time | DateTime | Timestamp of the transaction window |
| date_id | Integer | Foreign key to dim_time (YYYYMMDD format) |
| category | String | Product category |
| country | String | Country where sale occurred |
| total_amount | Double | Total sales amount |
| transaction_count | Integer | Number of transactions |
| avg_transaction_value | Double | Average transaction value |
| loaded_at | DateTime | ETL load timestamp |

**Purpose**: Stores aggregated sales metrics for analysis and reporting.

---

### 2. **fact_sessions**
Contains user session information and cart events.

| Field | Type | Description |
|-------|------|-------------|
| session_id | String | Unique session identifier |
| user_id | String | User identifier |
| start_time | DateTime | Session start time |
| end_time | DateTime | Session end time |
| duration_seconds | Integer | Session duration |
| page_views | Integer | Number of pages viewed |
| cart_adds | Integer | Items added to cart |
| cart_removes | Integer | Items removed from cart |
| purchase_completed | Boolean | Whether purchase was made |
| abandoned | Boolean | Whether cart was abandoned |
| total_amount | Double | Total purchase amount (if completed) |
| date_id | Integer | Foreign key to dim_time |
| loaded_at | DateTime | ETL load timestamp |

**Purpose**: Analyzes user behavior, session patterns, and cart abandonment.

---

## Dimension Tables

### 3. **dim_time**
Time dimension for temporal analysis.

| Field | Type | Description |
|-------|------|-------------|
| date_id | Integer | Primary key (YYYYMMDD) |
| date | Date | Full date |
| year | Integer | Year |
| quarter | Integer | Quarter (1-4) |
| month | Integer | Month (1-12) |
| month_name | String | Month name |
| week | Integer | Week of year |
| day | Integer | Day of month |
| day_of_week | Integer | Day of week (1-7) |
| day_name | String | Day name |
| is_weekend | Boolean | Weekend flag |

**Purpose**: Enables time-based analysis and aggregations.

---

### 4. **dim_customers** (Future Implementation)
Customer dimension for customer analysis.

| Field | Type | Description |
|-------|------|-------------|
| customer_id | String | Primary key |
| country | String | Customer country |
| registration_date | DateTime | Registration date |
| segment | String | Customer segment |
| total_purchases | Integer | Lifetime purchases |
| total_spent | Double | Lifetime value |

**Purpose**: Customer demographics and segmentation.

---

### 5. **dim_products** (Future Implementation)
Product dimension for product analytics.

| Field | Type | Description |
|-------|------|-------------|
| product_id | String | Primary key |
| name | String | Product name |
| category | String | Product category |
| price | Double | Product price |
| inventory | Integer | Current inventory |
| ratings | Double | Average rating |

**Purpose**: Product catalog and attributes.

---

## Analytical Collections

### 6. **customer_segments**
RFM Analysis results for customer segmentation.

| Field | Type | Description |
|-------|------|-------------|
| country | String | Customer country (proxy for customer_id) |
| recency | Integer | Days since last purchase |
| frequency | Integer | Number of purchases |
| monetary | Double | Total amount spent |
| r_score | Integer | Recency score (1-5) |
| f_score | Integer | Frequency score (1-5) |
| m_score | Integer | Monetary score (1-5) |
| rfm_segment | String | RFM code (e.g., "555") |
| segment_name | String | Segment name (e.g., "Champions") |
| analysis_date | DateTime | Analysis timestamp |

**Segments**:
- Champions (555-544)
- Loyal Customers (455-444)
- Potential Loyalists (355-344)
- New Customers (255-244)
- Promising (155-144)
- Need Attention
- At Risk
- Hibernating
- Cannot Lose Them
- Lost

**Purpose**: Customer segmentation for targeted marketing.

---

### 7. **product_performance**
Product category performance metrics.

| Field | Type | Description |
|-------|------|-------------|
| category | String | Product category |
| total_revenue | Double | Total revenue generated |
| total_transactions | Integer | Total transactions |
| avg_order_value | Double | Average order value |
| data_points | Integer | Number of data points |
| revenue_share | Double | Percentage of total revenue |
| performance_rating | String | Rating (Excellent/Good/Average/Below Average) |
| rank | Integer | Rank by revenue |
| analysis_date | DateTime | Analysis timestamp |

**Performance Ratings**:
- Excellent: >= 20% revenue share
- Good: >= 10% revenue share
- Average: >= 5% revenue share
- Below Average: < 5% revenue share

**Purpose**: Product performance analysis and inventory planning.

---

### 8. **sales_trends**
Sales trends over different time periods.

| Field | Type | Description |
|-------|------|-------------|
| period_type | String | Type (daily/weekly/monthly) |
| period | String | Period identifier |
| revenue | Double | Total revenue for period |
| transactions | Integer | Total transactions |
| revenue_growth_rate | Double | Growth rate percentage |
| analysis_date | DateTime | Analysis timestamp |

**Purpose**: Time-series analysis and forecasting.

---

## ETL Pipeline Flow

```
1. Extract from PostgreSQL
   ├── sales_metrics
   ├── session_metrics
   └── transaction_anomalies

2. Transform
   ├── Aggregate by dimensions
   ├── Calculate metrics
   └── Generate surrogate keys

3. Load to MongoDB
   ├── fact_sales
   ├── fact_sessions
   ├── dim_time
   ├── customer_segments (RFM)
   ├── product_performance
   └── sales_trends
```

---

## Batch Job Schedule

| Job | Frequency | Purpose |
|-----|-----------|---------|
| ETL Pipeline | Every 6 hours | Load data from operational DB |
| RFM Analysis | Daily at 2 AM | Update customer segments |
| Product Performance | Daily at 3 AM | Analyze product metrics |
| Sales Trends | Daily at 4 AM | Calculate trend metrics |

---

## Query Examples

### Get sales by category
```javascript
db.fact_sales.aggregate([
  {$group: {
    _id: "$category",
    total_revenue: {$sum: "$total_amount"},
    total_transactions: {$sum: "$transaction_count"}
  }},
  {$sort: {total_revenue: -1}}
])
```

### Get customer segments distribution
```javascript
db.customer_segments.aggregate([
  {$group: {
    _id: "$segment_name",
    count: {$sum: 1},
    avg_monetary: {$avg: "$monetary"}
  }}
])
```

### Get sales trends
```javascript
db.sales_trends.find({period_type: "monthly"}).sort({period: -1})
```

---

## Data Freshness

- **Real-time Data**: PostgreSQL (< 1 minute lag)
- **Data Warehouse**: MongoDB (Updated every 6 hours)
- **Analytics**: Daily batch updates

---

## Scalability Considerations

1. **Partitioning**: MongoDB collections can be sharded by date_id or country
2. **Indexes**: Create indexes on frequently queried fields:
   - fact_sales: (date_id, category, country)
   - customer_segments: (segment_name, country)
   - product_performance: (rank, category)
3. **Archiving**: Move old data (> 2 years) to archive collections

---

## Future Enhancements

1. Implement dim_customers with actual user data
2. Implement dim_products with product catalog
3. Add fact_inventory for inventory tracking
4. Add slowly changing dimensions (SCD Type 2)
5. Implement data quality checks and monitoring
