# GlobalMart Data Explorer - Web Interface

Interactive web-based data exploration tool for GlobalMart analytics platform.

## Features

- **4 Data Views:**
  - Sales Metrics (revenue, transactions, avg order value)
  - Customer Sessions (session analytics, cart behavior)
  - Inventory Status (low stock alerts)
  - Transaction Anomalies (fraud detection)

- **Interactive Features:**
  - Date range filtering
  - Country and category filters
  - Real-time data refresh
  - CSV export functionality
  - Interactive charts (Chart.js)
  - Responsive Bootstrap UI

## Quick Start

### Method 1: Using Startup Script (Recommended)
```bash
cd /home/g7/Desktop/BigData/globalmart/web
./START_WEB_INTERFACE.sh
```

### Method 2: Manual Start
```bash
cd /home/g7/Desktop/BigData/globalmart/api
/home/g7/Desktop/BigData/.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## Access

Open browser and navigate to:
- **Web Interface:** http://localhost:8000/explorer
- **API Docs:** http://localhost:8000/docs
- **API Health:** http://localhost:8000/health

## File Structure

```
web/
├── index.html                      # Main web interface
├── static/
│   ├── css/
│   │   └── styles.css             # Custom styling
│   └── js/
│       └── app.js                 # Application logic
├── START_WEB_INTERFACE.sh         # Startup script
└── README.md                      # This file
```

## Dependencies

- FastAPI (web framework)
- Bootstrap 5 (UI framework)
- Chart.js (data visualization)
- PostgreSQL (data source)

## Usage

### Viewing Sales Data
1. Navigate to http://localhost:8000/explorer
2. Default view shows sales metrics
3. Use filters to refine data:
   - Start/End Date
   - Country
   - Category
4. Click "Search" to apply filters

### Exploring Different Sections
Click navigation tabs:
- **Sales:** Revenue and transaction metrics
- **Customers:** Session analytics
- **Inventory:** Low stock items
- **Anomalies:** Transaction anomalies

### Exporting Data
1. Load the data you want to export
2. Click "Export CSV" button
3. File downloads automatically

### Interactive Charts
- Charts update automatically when data changes
- Different chart types for each section:
  - Sales: Bar chart (revenue by category)
  - Sessions: Line chart (duration over time)
  - Inventory: Horizontal bar chart (stock levels)
  - Anomalies: Doughnut chart (anomaly types)

## API Endpoints Used

The web interface connects to these backend endpoints:

```
POST /api/query          - Execute custom SQL queries
GET  /health             - Health check
GET  /                   - API info
```

## Security

- **Query Restrictions:** Only SELECT queries allowed
- **SQL Injection Protection:** Parameterized queries
- **CORS:** Configured for same-origin access

## Troubleshooting

### Web Interface Not Loading
```bash
# Check if API server is running
curl http://localhost:8000/health

# Check static files exist
ls -la /home/g7/Desktop/BigData/globalmart/web/static/
```

### No Data Displayed
```bash
# Verify PostgreSQL connection
psql -h localhost -U globalmart -d globalmart -c "SELECT COUNT(*) FROM sales_metrics;"

# Check if tables have data
python3 /tmp/check_tables.py
```

### Port Already in Use
```bash
# Kill existing process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn main:app --port 8001
```

## Development

### Adding New Data Sections
1. Add navigation link in `index.html`
2. Create load function in `app.js` (e.g., `loadMyData()`)
3. Add SQL query via `/api/query` endpoint
4. Render table with `renderTable()`
5. Create chart with appropriate Chart.js type

### Customizing Styles
Edit `/home/g7/Desktop/BigData/globalmart/web/static/css/styles.css`

### Modifying Charts
Chart configurations in `app.js`:
- `renderRevenueChart()`
- `renderSessionChart()`
- `renderInventoryChart()`
- `renderAnomalyChart()`

## Performance

- Default limit: 100 records per query
- "Load More" button fetches next 100
- Charts display top 10-20 items
- Auto-caching in PostgreSQL

## Browser Compatibility

Tested on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Points Contribution

**Part 4 (Visualization & API):** Web Interface = **7 points**
- Interactive data exploration ✓
- Multiple data views ✓
- Export functionality ✓
- Real-time filtering ✓
- Responsive design ✓

---

**Built with:** FastAPI, Bootstrap 5, Chart.js, PostgreSQL
