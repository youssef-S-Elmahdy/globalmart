-- GlobalMart Database Schema

-- Real-time sales metrics
CREATE TABLE sales_metrics (
    id SERIAL PRIMARY KEY,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    category VARCHAR(100),
    country VARCHAR(50),
    total_amount DECIMAL(12, 2),
    transaction_count INTEGER,
    avg_transaction_value DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(window_start, category, country)
);

CREATE INDEX idx_sales_metrics_window ON sales_metrics(window_start, window_end);
CREATE INDEX idx_sales_metrics_category ON sales_metrics(category);
CREATE INDEX idx_sales_metrics_country ON sales_metrics(country);

-- Inventory tracking
CREATE TABLE inventory_status (
    product_id VARCHAR(100) PRIMARY KEY,
    product_name VARCHAR(255),
    category VARCHAR(100),
    current_stock INTEGER,
    reserved_stock INTEGER,
    available_stock INTEGER,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_inventory_category ON inventory_status(category);
CREATE INDEX idx_inventory_stock ON inventory_status(available_stock);

-- Low stock alerts
CREATE TABLE low_stock_alerts (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(100),
    product_name VARCHAR(255),
    category VARCHAR(100),
    current_stock INTEGER,
    threshold INTEGER DEFAULT 10,
    alert_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active'
);

CREATE INDEX idx_low_stock_product ON low_stock_alerts(product_id);
CREATE INDEX idx_low_stock_status ON low_stock_alerts(status);

-- Anomaly detection results
CREATE TABLE transaction_anomalies (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(100) UNIQUE,
    user_id VARCHAR(100),
    amount DECIMAL(12, 2),
    anomaly_score DECIMAL(5, 4),
    anomaly_type VARCHAR(50),
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

CREATE INDEX idx_anomalies_user ON transaction_anomalies(user_id);
CREATE INDEX idx_anomalies_time ON transaction_anomalies(detected_at);

-- Session analysis
CREATE TABLE session_metrics (
    session_id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(100),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    page_views INTEGER,
    cart_adds INTEGER,
    cart_removes INTEGER,
    purchase_completed BOOLEAN DEFAULT FALSE,
    abandoned BOOLEAN DEFAULT FALSE,
    total_amount DECIMAL(12, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_session_user ON session_metrics(user_id);
CREATE INDEX idx_session_abandoned ON session_metrics(abandoned);
CREATE INDEX idx_session_time ON session_metrics(start_time);

-- Cart abandonment tracking
CREATE TABLE cart_abandonment (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100),
    user_id VARCHAR(100),
    products_in_cart INTEGER,
    cart_value DECIMAL(12, 2),
    abandonment_time TIMESTAMP,
    time_in_cart_minutes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_abandonment_user ON cart_abandonment(user_id);
CREATE INDEX idx_abandonment_time ON cart_abandonment(abandonment_time);

-- Real-time dashboard metrics
CREATE TABLE dashboard_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100),
    metric_value DECIMAL(15, 2),
    metric_type VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dashboard_name ON dashboard_metrics(metric_name);
CREATE INDEX idx_dashboard_time ON dashboard_metrics(timestamp);