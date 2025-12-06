"""
Pydantic models for API
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class SalesMetric(BaseModel):
    """Sales metrics model"""
    window_start: datetime
    window_end: datetime
    category: Optional[str] = None
    country: Optional[str] = None
    total_amount: float
    transaction_count: int
    avg_transaction_value: float

class CustomerSegment(BaseModel):
    """Customer segmentation model"""
    user_id: str
    recency: int
    frequency: int
    monetary: float
    r_score: int
    f_score: int
    m_score: int
    rfm_segment: str
    analysis_date: datetime

class ProductPerformance(BaseModel):
    """Product performance model"""
    product_id: str
    product_name: str
    category: str
    units_sold: int
    total_revenue: float
    avg_price: float
    performance_score: float
    rank_in_category: int

class TransactionAnomaly(BaseModel):
    """Transaction anomaly model"""
    transaction_id: str
    user_id: str
    amount: float
    anomaly_score: float
    anomaly_type: str
    detected_at: datetime
    description: str

class DashboardMetrics(BaseModel):
    """Dashboard summary metrics"""
    total_revenue_today: float
    total_transactions_today: int
    avg_transaction_value: float
    active_users: int
    top_category: str
    top_country: str
    anomalies_count: int

class APIResponse(BaseModel):
    """Standard API response"""
    success: bool
    message: str
    data: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
