#!/usr/bin/env python3
"""
GlobalMart Executive Dashboard - Python Alternative to Power BI
Uses Streamlit for interactive web-based dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="GlobalMart Executive Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# MongoDB connection
@st.cache_resource
def get_mongo_client():
    uri = 'mongodb://globalmart:globalmart123@localhost:27017/globalmart_dw?authSource=admin'
    return MongoClient(uri)

@st.cache_data(ttl=600)  # Cache for 10 minutes
def load_data():
    """Load all data from MongoDB"""
    client = get_mongo_client()
    db = client['globalmart_dw']

    data = {
        'sales_trends': pd.DataFrame(list(db.sales_trends.find())),
        'customer_segments': pd.DataFrame(list(db.customer_segments.find())),
        'product_performance': pd.DataFrame(list(db.product_performance.find())),
        'fact_sales': pd.DataFrame(list(db.fact_sales.find())),
        'fact_sessions': pd.DataFrame(list(db.fact_sessions.find().limit(1000)))  # Sample for performance
    }

    # Clean data
    for df_name, df in data.items():
        if '_id' in df.columns:
            df.drop('_id', axis=1, inplace=True)

    return data

# Load data
try:
    data = load_data()
except Exception as e:
    st.error(f"Error connecting to MongoDB: {e}")
    st.stop()

# Sidebar
st.sidebar.title("📊 GlobalMart Analytics")
st.sidebar.markdown("---")

# Page selection
page = st.sidebar.radio(
    "Select Dashboard Page",
    ["Executive Overview", "Geographic Analysis", "Product Performance", "Customer Insights"]
)

# Date filter
if not data['sales_trends'].empty and 'analysis_date' in data['sales_trends'].columns:
    date_range = st.sidebar.selectbox(
        "Date Range",
        ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"]
    )

# Country filter
if not data['customer_segments'].empty and 'country' in data['customer_segments'].columns:
    countries = ['All'] + sorted(data['customer_segments']['country'].dropna().unique().tolist())
    selected_country = st.sidebar.selectbox("Country", countries)
else:
    selected_country = 'All'

st.sidebar.markdown("---")
st.sidebar.markdown("**Last Updated:**")
st.sidebar.markdown(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ============================================================================
# PAGE 1: EXECUTIVE OVERVIEW
# ============================================================================
if page == "Executive Overview":
    st.title("📈 Executive Overview")

    # KPIs
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_revenue = data['sales_trends']['revenue'].sum() if 'revenue' in data['sales_trends'].columns else 0
        st.metric("Total Revenue", f"${total_revenue:,.2f}")

    with col2:
        total_transactions = data['sales_trends']['transactions'].sum() if 'transactions' in data['sales_trends'].columns else 0
        st.metric("Total Transactions", f"{total_transactions:,}")

    with col3:
        avg_order = total_revenue / total_transactions if total_transactions > 0 else 0
        st.metric("Avg Order Value", f"${avg_order:,.2f}")

    with col4:
        growth_rate = data['sales_trends']['revenue_growth_rate'].mean() * 100 if 'revenue_growth_rate' in data['sales_trends'].columns else 0
        st.metric("Growth Rate", f"{growth_rate:.2f}%")

    st.markdown("---")

    # Revenue Trend
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Revenue Trend")
        if not data['sales_trends'].empty:
            fig = px.line(
                data['sales_trends'],
                x='period',
                y='revenue',
                color='period_type',
                title="Revenue Over Time"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Customer Segment Distribution")
        if not data['customer_segments'].empty and 'segment_name' in data['customer_segments'].columns:
            segment_counts = data['customer_segments']['segment_name'].value_counts()
            fig = px.pie(
                values=segment_counts.values,
                names=segment_counts.index,
                title="Customer Segments"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# PAGE 2: GEOGRAPHIC ANALYSIS
# ============================================================================
elif page == "Geographic Analysis":
    st.title("🌍 Sales by Geography")

    # Filter by country
    df_geo = data['customer_segments'].copy()
    if selected_country != 'All':
        df_geo = df_geo[df_geo['country'] == selected_country]

    # Country metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        total_countries = len(data['customer_segments']['country'].unique()) if 'country' in data['customer_segments'].columns else 0
        st.metric("Total Countries", total_countries)

    with col2:
        top_country = df_geo.groupby('country')['monetary'].sum().idxmax() if not df_geo.empty else "N/A"
        st.metric("Top Country", top_country)

    with col3:
        total_customers = len(df_geo) if not df_geo.empty else 0
        st.metric("Total Customers", f"{total_customers:,}")

    st.markdown("---")

    # Revenue by Country
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Revenue by Country")
        if not df_geo.empty and 'country' in df_geo.columns:
            country_revenue = df_geo.groupby('country')['monetary'].sum().sort_values(ascending=False)
            fig = px.bar(
                x=country_revenue.index,
                y=country_revenue.values,
                labels={'x': 'Country', 'y': 'Revenue ($)'},
                title="Revenue Distribution by Country"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Top Countries Table")
        if not df_geo.empty:
            country_stats = df_geo.groupby('country').agg({
                'monetary': 'sum',
                'frequency': 'sum',
                'segment_name': 'count'
            }).round(2)
            country_stats.columns = ['Revenue', 'Transactions', 'Customers']
            country_stats = country_stats.sort_values('Revenue', ascending=False)
            st.dataframe(country_stats.head(10), use_container_width=True)

# ============================================================================
# PAGE 3: PRODUCT PERFORMANCE
# ============================================================================
elif page == "Product Performance":
    st.title("📦 Product Category Analysis")

    # Category metrics from fact_sales
    if not data['fact_sales'].empty and 'category' in data['fact_sales'].columns:
        df_products = data['fact_sales'].copy()

        # Aggregate by category
        category_stats = df_products.groupby('category').agg({
            'total_amount': 'sum',
            'transaction_count': 'sum',
            'avg_transaction_value': 'mean'
        }).round(2)
        category_stats.columns = ['Revenue', 'Transactions', 'Avg Order Value']
        category_stats = category_stats.sort_values('Revenue', ascending=False)

        # KPIs
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Categories", len(category_stats))

        with col2:
            top_category = category_stats.index[0] if not category_stats.empty else "N/A"
            st.metric("Top Category", top_category)

        with col3:
            total_revenue = category_stats['Revenue'].sum()
            st.metric("Total Revenue", f"${total_revenue:,.2f}")

        st.markdown("---")

        # Visualizations
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Revenue Share by Category")
            fig = px.pie(
                values=category_stats['Revenue'],
                names=category_stats.index,
                title="Category Revenue Distribution"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Top 10 Categories")
            fig = px.bar(
                x=category_stats.head(10).index,
                y=category_stats.head(10)['Revenue'],
                labels={'x': 'Category', 'y': 'Revenue ($)'},
                title="Top Categories by Revenue"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        # Category performance table
        st.subheader("Category Performance Details")
        st.dataframe(category_stats, use_container_width=True)
    else:
        st.warning("No product data available. Run batch ETL jobs to populate data.")

# ============================================================================
# PAGE 4: CUSTOMER INSIGHTS
# ============================================================================
elif page == "Customer Insights":
    st.title("👥 Customer Segmentation & RFM Analysis")

    df_customers = data['customer_segments'].copy()

    if not df_customers.empty:
        # KPIs
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_customers = len(df_customers)
            st.metric("Total Customers", f"{total_customers:,}")

        with col2:
            champions = len(df_customers[df_customers['segment_name'] == 'Champions']) if 'segment_name' in df_customers.columns else 0
            st.metric("Champions", champions)

        with col3:
            avg_frequency = df_customers['frequency'].mean() if 'frequency' in df_customers.columns else 0
            st.metric("Avg Frequency", f"{avg_frequency:,.0f}")

        with col4:
            avg_monetary = df_customers['monetary'].mean() if 'monetary' in df_customers.columns else 0
            st.metric("Avg Monetary", f"${avg_monetary:,.2f}")

        st.markdown("---")

        # Visualizations
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("RFM Segment Distribution")
            if 'segment_name' in df_customers.columns:
                segment_counts = df_customers['segment_name'].value_counts()
                fig = px.bar(
                    x=segment_counts.index,
                    y=segment_counts.values,
                    labels={'x': 'Segment', 'y': 'Customer Count'},
                    title="Customers by Segment"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Segment Value")
            if 'segment_name' in df_customers.columns and 'monetary' in df_customers.columns:
                segment_value = df_customers.groupby('segment_name')['monetary'].sum().sort_values(ascending=False)
                fig = px.bar(
                    x=segment_value.index,
                    y=segment_value.values,
                    labels={'x': 'Segment', 'y': 'Total Value ($)'},
                    title="Monetary Value by Segment"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

        # Segment metrics table
        st.subheader("Segment Metrics")
        segment_metrics = df_customers.groupby('segment_name').agg({
            'frequency': 'mean',
            'monetary': 'mean',
            'segment_name': 'count'
        }).round(2)
        segment_metrics.columns = ['Avg Frequency', 'Avg Monetary', 'Customer Count']
        st.dataframe(segment_metrics, use_container_width=True)

        # RFM Scores Scatter
        if all(col in df_customers.columns for col in ['frequency', 'monetary', 'segment_name']):
            st.subheader("RFM Analysis Scatter Plot")
            fig = px.scatter(
                df_customers,
                x='frequency',
                y='monetary',
                color='segment_name',
                title="Frequency vs Monetary Value by Segment",
                labels={'frequency': 'Frequency (Orders)', 'monetary': 'Monetary Value ($)'}
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No customer segment data available. Run RFM analysis batch job.")

# Footer
st.markdown("---")
st.markdown("**GlobalMart Executive Dashboard** | Powered by Python, Streamlit & MongoDB | 🤖 Generated with Claude Code")
