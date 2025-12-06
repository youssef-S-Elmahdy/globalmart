"""
GlobalMart Analytics API
"""

from fastapi import FastAPI, HTTPException, Depends, Query, Security, Request
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from pathlib import Path
import json

import config
from database import db
from models import *

# Initialize FastAPI app
app = FastAPI(
    title=config.API_TITLE,
    version=config.API_VERSION,
    description=config.API_DESCRIPTION
)

# Mount static files for web interface
web_dir = Path(__file__).parent.parent / "web"
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir / "static")), name="static")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: Optional[str] = Security(api_key_header)):
    """Verify API key"""
    if api_key != config.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": config.API_VERSION
    }

# Sales Metrics Endpoints
@app.get("/api/v1/sales/metrics")
async def get_sales_metrics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Product category"),
    country: Optional[str] = Query(None, description="Country"),
    limit: int = Query(100, ge=1, le=1000),
    api_key: str = Depends(verify_api_key)
):
    """
    Get sales metrics with optional filters
    """
    try:
        with db.get_postgres_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT window_start, window_end, category, country,
                       total_amount, transaction_count, avg_transaction_value
                FROM sales_metrics
                WHERE 1=1
            """
            params = []

            if start_date:
                query += " AND window_start >= %s"
                params.append(start_date)

            if end_date:
                query += " AND window_end <= %s"
                params.append(end_date)

            if category:
                query += " AND category = %s"
                params.append(category)

            if country:
                query += " AND country = %s"
                params.append(country)

            query += " ORDER BY window_start DESC LIMIT %s"
            params.append(limit)

            cursor.execute(query, params)
            results = cursor.fetchall()

            return {"sales_metrics": results, "count": len(results)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/sales/summary")
async def get_sales_summary(
    period: str = Query("today", description="Period: today, week, month"),
    api_key: str = Depends(verify_api_key)
):
    """
    Get sales summary for specified period
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        if period == "today":
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_date = end_date - timedelta(days=7)
        elif period == "month":
            start_date = end_date - timedelta(days=30)
        else:
            raise HTTPException(status_code=400, detail="Invalid period")

        with db.get_postgres_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    COUNT(*) as transaction_count,
                    COALESCE(SUM(total_amount), 0) as total_revenue,
                    COALESCE(AVG(total_amount), 0) as avg_transaction_value,
                    COALESCE(MIN(total_amount), 0) as min_transaction,
                    COALESCE(MAX(total_amount), 0) as max_transaction
                FROM sales_metrics
                WHERE window_start >= %s AND window_end <= %s
            """

            cursor.execute(query, (start_date, end_date))
            result = cursor.fetchone()

            return {
                "period": period,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "metrics": dict(result) if result else {}
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Customer Segmentation Endpoints
@app.get("/api/v1/customers/segments")
async def get_customer_segments(
    segment: Optional[str] = Query(None, description="RFM segment"),
    limit: int = Query(100, ge=1, le=1000),
    api_key: str = Depends(verify_api_key)
):
    """
    Get customer segmentation data
    """
    try:
        mongo_db = db.get_mongodb_client()
        collection = mongo_db.customer_segments

        query = {}
        if segment:
            query['rfm_segment'] = segment

        results = list(collection.find(query, {'_id': 0}).limit(limit))

        return {"segments": results, "count": len(results)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/customers/segments/distribution")
async def get_segment_distribution(
    api_key: str = Depends(verify_api_key)
):
    """Get distribution of customers across segments"""
    try:
        mongo_db = db.get_mongodb_client()
        collection = mongo_db.customer_segments

        pipeline = [
            {
                "$group": {
                    "_id": "$rfm_segment",
                    "count": {"$sum": 1},
                    "avg_monetary": {"$avg": "$monetary"},
                    "total_monetary": {"$sum": "$monetary"}
                }
            },
            {
                "$sort": {"count": -1}
            }
        ]

        results = list(collection.aggregate(pipeline))

        return {
            "segments": [
                {
                    "segment": r['_id'] if r['_id'] else "Unknown",
                    "customer_count": r['count'],
                    "avg_customer_value": round(r.get('avg_monetary', 0), 2),
                    "total_segment_value": round(r.get('total_monetary', 0), 2)
                }
                for r in results
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Product Performance Endpoints
@app.get("/api/v1/products/performance")
async def get_product_performance(
    category: Optional[str] = Query(None, description="Product category"),
    sort_by: str = Query("total_revenue", description="Sort by: total_revenue, units_sold, performance_score"),
    limit: int = Query(100, ge=1, le=1000),
    api_key: str = Depends(verify_api_key)
):
    """Get product performance metrics"""
    try:
        mongo_db = db.get_mongodb_client()
        collection = mongo_db.product_performance

        query = {}
        if category:
            query['category'] = category

        sort_field = sort_by if sort_by in ['total_revenue', 'units_sold', 'performance_score'] else 'total_revenue'

        results = list(collection.find(query, {'_id': 0}).sort(sort_field, -1).limit(limit))

        return {"products": results, "count": len(results)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/products/top-performers")
async def get_top_performers(
    top_n: int = Query(10, ge=1, le=100),
    api_key: str = Depends(verify_api_key)
):
    """Get top performing products"""
    try:
        mongo_db = db.get_mongodb_client()
        collection = mongo_db.product_performance

        pipeline = [
            {"$sort": {"total_revenue": -1}},
            {"$limit": top_n},
            {
                "$project": {
                    "_id": 0,
                    "product_id": 1,
                    "product_name": 1,
                    "category": 1,
                    "total_revenue": 1,
                    "units_sold": 1
                }
            }
        ]

        results = list(collection.aggregate(pipeline))

        return {"top_products": results, "count": len(results)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Anomaly Detection Endpoints
@app.get("/api/v1/anomalies")
async def get_anomalies(
    limit: int = Query(100, ge=1, le=1000),
    api_key: str = Depends(verify_api_key)
):
    """Get recent transaction anomalies"""
    try:
        with db.get_postgres_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT transaction_id, user_id, product_id, amount,
                       anomaly_score, anomaly_type, detected_at, description
                FROM transaction_anomalies
                ORDER BY detected_at DESC
                LIMIT %s
            """

            cursor.execute(query, (limit,))
            results = cursor.fetchall()

            return {"anomalies": results, "count": len(results)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Dashboard Endpoint
@app.get("/api/v1/dashboard")
async def get_dashboard_metrics(
    api_key: str = Depends(verify_api_key)
):
    """Get dashboard summary metrics"""
    try:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        with db.get_postgres_connection() as conn:
            cursor = conn.cursor()

            # Sales metrics
            cursor.execute("""
                SELECT
                    COALESCE(SUM(total_amount), 0) as revenue,
                    COALESCE(SUM(transaction_count), 0) as transactions,
                    COALESCE(AVG(avg_transaction_value), 0) as avg_value
                FROM sales_metrics
                WHERE window_start >= %s
            """, (today,))
            sales_result = cursor.fetchone()

            # Anomalies count
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM transaction_anomalies
                WHERE detected_at >= %s
            """, (today,))
            anomalies_result = cursor.fetchone()

        # MongoDB metrics
        mongo_db = db.get_mongodb_client()

        # Top category
        top_category_pipeline = [
            {"$sort": {"total_revenue": -1}},
            {"$limit": 1},
            {"$project": {"category": 1, "_id": 0}}
        ]
        top_category = list(mongo_db.product_performance.aggregate(top_category_pipeline))

        return {
            "total_revenue_today": float(sales_result['revenue']),
            "total_transactions_today": int(sales_result['transactions']),
            "avg_transaction_value": float(sales_result['avg_value']),
            "anomalies_count": int(anomalies_result['count']),
            "top_category": top_category[0]['category'] if top_category else "N/A",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Web Interface Endpoints
@app.get("/explorer", response_class=HTMLResponse)
async def web_explorer():
    """Serve the data explorer web interface"""
    index_path = Path(__file__).parent.parent / "web" / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Web interface not found")

@app.post("/api/query")
async def execute_query(request: Request):
    """Execute custom SQL query (for web interface)"""
    try:
        body = await request.json()
        query = body.get('query', '')

        if not query:
            raise HTTPException(status_code=400, detail="Query is required")

        # Security: Only allow SELECT queries
        if not query.strip().upper().startswith('SELECT'):
            raise HTTPException(status_code=403, detail="Only SELECT queries are allowed")

        with db.get_postgres_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)

            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            # Fetch data
            rows = cursor.fetchall()

            # Convert to list of dicts
            data = []
            for row in rows:
                data.append({columns[i]: row[i] for i in range(len(columns))})

            return {"data": data, "count": len(data)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "GlobalMart Analytics API",
        "version": config.API_VERSION,
        "docs": "/docs",
        "health": "/health",
        "explorer": "/explorer"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
