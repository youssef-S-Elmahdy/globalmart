// GlobalMart Data Explorer - Main Application Logic

// Configuration
const API_BASE_URL = 'http://localhost:8000';  // Will be served from same FastAPI server
const DB_CONFIG = {
    host: 'localhost',
    port: 5432,
    database: 'globalmart',
    user: 'globalmart',
    password: 'globalmart123'
};

// State
let currentSection = 'sales';
let currentData = [];
let currentChart = null;
let currentOffset = 0;
const LIMIT = 100;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('GlobalMart Data Explorer initialized');

    // Set default dates (last 30 days)
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);

    document.getElementById('endDate').valueAsDate = endDate;
    document.getElementById('startDate').valueAsDate = startDate;

    // Setup navigation
    setupNavigation();

    // Load initial data
    loadSection('sales');
});

// Navigation setup
function setupNavigation() {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();

            // Update active state
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            this.classList.add('active');

            // Load section
            const section = this.dataset.section;
            loadSection(section);
        });
    });
}

// Load data section
async function loadSection(section) {
    currentSection = section;
    currentOffset = 0;

    showLoading(true);

    try {
        switch(section) {
            case 'sales':
                await loadSalesData();
                break;
            case 'customers':
                await loadCustomerData();
                break;
            case 'inventory':
                await loadInventoryData();
                break;
            case 'anomalies':
                await loadAnomalyData();
                break;
        }

        updateStats();
    } catch (error) {
        console.error('Error loading section:', error);
        showError('Failed to load data. Please try again.');
    } finally {
        showLoading(false);
    }
}

// Load sales data from PostgreSQL
async function loadSalesData() {
    const data = await fetchFromDB(`
        SELECT
            window_start,
            window_end,
            category,
            country,
            total_amount,
            transaction_count,
            avg_transaction_value
        FROM sales_metrics
        ORDER BY window_start DESC
        LIMIT ${LIMIT} OFFSET ${currentOffset}
    `);

    currentData = data;

    // Update table
    document.getElementById('tableTitle').textContent = 'Sales Metrics';
    renderTable([
        'Start Time',
        'End Time',
        'Category',
        'Country',
        'Revenue',
        'Transactions',
        'Avg Value'
    ], data, [
        'window_start',
        'window_end',
        'category',
        'country',
        'total_amount',
        'transaction_count',
        'avg_transaction_value'
    ]);

    // Update chart
    renderRevenueChart(data);
}

// Load customer segment data
async function loadCustomerData() {
    const data = await fetchFromDB(`
        SELECT
            session_id,
            user_id,
            start_time,
            duration_seconds,
            page_views,
            cart_adds,
            abandoned
        FROM session_metrics
        ORDER BY start_time DESC
        LIMIT ${LIMIT} OFFSET ${currentOffset}
    `);

    currentData = data;

    document.getElementById('tableTitle').textContent = 'Customer Sessions';
    renderTable([
        'Session ID',
        'User ID',
        'Start Time',
        'Duration (s)',
        'Page Views',
        'Cart Adds',
        'Abandoned'
    ], data, [
        'session_id',
        'user_id',
        'start_time',
        'duration_seconds',
        'page_views',
        'cart_adds',
        'abandoned'
    ]);

    renderSessionChart(data);
}

// Load inventory data
async function loadInventoryData() {
    const data = await fetchFromDB(`
        SELECT
            product_id,
            product_name,
            category,
            current_stock,
            reserved_stock,
            available_stock,
            last_updated
        FROM inventory_status
        WHERE available_stock < 100
        ORDER BY available_stock ASC
        LIMIT ${LIMIT} OFFSET ${currentOffset}
    `);

    currentData = data;

    document.getElementById('tableTitle').textContent = 'Low Stock Items';
    renderTable([
        'Product ID',
        'Product Name',
        'Category',
        'Current Stock',
        'Reserved',
        'Available',
        'Last Updated'
    ], data, [
        'product_id',
        'product_name',
        'category',
        'current_stock',
        'reserved_stock',
        'available_stock',
        'last_updated'
    ]);

    renderInventoryChart(data);
}

// Load anomaly data
async function loadAnomalyData() {
    const data = await fetchFromDB(`
        SELECT
            transaction_id,
            user_id,
            amount,
            anomaly_score,
            anomaly_type,
            detected_at,
            description
        FROM transaction_anomalies
        ORDER BY detected_at DESC
        LIMIT ${LIMIT} OFFSET ${currentOffset}
    `);

    currentData = data;

    document.getElementById('tableTitle').textContent = 'Transaction Anomalies';
    renderTable([
        'Transaction ID',
        'User ID',
        'Amount',
        'Score',
        'Type',
        'Detected At',
        'Description'
    ], data, [
        'transaction_id',
        'user_id',
        'amount',
        'anomaly_score',
        'anomaly_type',
        'detected_at',
        'description'
    ]);

    renderAnomalyChart(data);
}

// Fetch data from PostgreSQL via backend
async function fetchFromDB(query) {
    try {
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        return result.data || [];
    } catch (error) {
        console.error('Database query error:', error);

        // Fallback to mock data for demo
        return generateMockData(query);
    }
}

// Generate mock data for demo purposes
function generateMockData(query) {
    if (query.includes('sales_metrics')) {
        return Array.from({length: 50}, (_, i) => ({
            window_start: new Date(Date.now() - i * 3600000).toISOString(),
            window_end: new Date(Date.now() - i * 3600000 + 3600000).toISOString(),
            category: ['Electronics', 'Clothing', 'Home', 'Sports'][i % 4],
            country: ['USA', 'UK', 'Canada', 'Germany'][i % 4],
            total_amount: (Math.random() * 100000 + 10000).toFixed(2),
            transaction_count: Math.floor(Math.random() * 1000 + 100),
            avg_transaction_value: (Math.random() * 200 + 50).toFixed(2)
        }));
    }
    return [];
}

// Render table
function renderTable(headers, data, fields) {
    const thead = document.getElementById('tableHeader');
    const tbody = document.getElementById('tableBody');

    // Render headers
    thead.innerHTML = headers.map(h => `<th>${h}</th>`).join('');

    // Render data
    tbody.innerHTML = data.map(row => {
        return '<tr>' + fields.map(field => {
            let value = row[field];

            // Format values
            if (field.includes('amount') || field.includes('value')) {
                value = '$' + parseFloat(value || 0).toLocaleString('en-US', {minimumFractionDigits: 2});
            } else if (field.includes('time') || field.includes('updated')) {
                value = new Date(value).toLocaleString();
            } else if (field === 'abandoned') {
                value = value ? '<span class="badge bg-danger">Yes</span>' : '<span class="badge bg-success">No</span>';
            } else if (typeof value === 'number') {
                value = value.toLocaleString();
            }

            return `<td>${value || 'N/A'}</td>`;
        }).join('') + '</tr>';
    }).join('');

    document.getElementById('recordCount').textContent = data.length;
}

// Update statistics cards
function updateStats() {
    if (currentSection === 'sales' && currentData.length > 0) {
        const totalRevenue = currentData.reduce((sum, row) => sum + parseFloat(row.total_amount || 0), 0);
        const totalTransactions = currentData.reduce((sum, row) => sum + parseInt(row.transaction_count || 0), 0);
        const avgOrder = totalRevenue / totalTransactions;

        document.getElementById('totalRevenue').textContent = '$' + totalRevenue.toLocaleString('en-US', {minimumFractionDigits: 2});
        document.getElementById('totalTransactions').textContent = totalTransactions.toLocaleString();
        document.getElementById('avgOrderValue').textContent = '$' + avgOrder.toLocaleString('en-US', {minimumFractionDigits: 2});
    }
}

// Chart rendering functions
function renderRevenueChart(data) {
    const ctx = document.getElementById('dataChart');

    if (currentChart) {
        currentChart.destroy();
    }

    const categories = [...new Set(data.map(d => d.category))];
    const revenueByCategory = categories.map(cat => {
        return data.filter(d => d.category === cat)
                   .reduce((sum, d) => sum + parseFloat(d.total_amount || 0), 0);
    });

    currentChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categories,
            datasets: [{
                label: 'Revenue by Category',
                data: revenueByCategory,
                backgroundColor: 'rgba(13, 110, 253, 0.7)',
                borderColor: 'rgba(13, 110, 253, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

function renderSessionChart(data) {
    const ctx = document.getElementById('dataChart');

    if (currentChart) {
        currentChart.destroy();
    }

    currentChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.slice(0, 20).map((d, i) => `Session ${i + 1}`),
            datasets: [{
                label: 'Duration (seconds)',
                data: data.slice(0, 20).map(d => d.duration_seconds),
                borderColor: 'rgba(13, 202, 240, 1)',
                backgroundColor: 'rgba(13, 202, 240, 0.2)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

function renderInventoryChart(data) {
    const ctx = document.getElementById('dataChart');

    if (currentChart) {
        currentChart.destroy();
    }

    currentChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.slice(0, 10).map(d => d.product_name?.substring(0, 20) || d.product_id),
            datasets: [{
                label: 'Available Stock',
                data: data.slice(0, 10).map(d => d.available_stock),
                backgroundColor: 'rgba(255, 193, 7, 0.7)',
                borderColor: 'rgba(255, 193, 7, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y'
        }
    });
}

function renderAnomalyChart(data) {
    const ctx = document.getElementById('dataChart');

    if (currentChart) {
        currentChart.destroy();
    }

    const types = [...new Set(data.map(d => d.anomaly_type))];
    const countByType = types.map(type => data.filter(d => d.anomaly_type === type).length);

    currentChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: types,
            datasets: [{
                data: countByType,
                backgroundColor: [
                    'rgba(220, 53, 69, 0.7)',
                    'rgba(255, 193, 7, 0.7)',
                    'rgba(13, 110, 253, 0.7)',
                    'rgba(25, 135, 84, 0.7)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

// Filter and search
function applyFilters() {
    currentOffset = 0;
    loadSection(currentSection);
}

// Load more data
function loadMore() {
    currentOffset += LIMIT;
    loadSection(currentSection);
}

// Export to CSV
function exportToCSV() {
    if (currentData.length === 0) {
        alert('No data to export');
        return;
    }

    const headers = Object.keys(currentData[0]);
    const csv = [
        headers.join(','),
        ...currentData.map(row =>
            headers.map(h => JSON.stringify(row[h] || '')).join(',')
        )
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `globalmart_${currentSection}_${new Date().toISOString()}.csv`;
    a.click();
}

// Utility functions
function showLoading(show) {
    const modal = new bootstrap.Modal(document.getElementById('loadingModal'));
    if (show) {
        modal.show();
    } else {
        modal.hide();
    }
}

function showError(message) {
    alert(message);
}
