"""
Notification Service Configuration
Update these settings for your environment
"""

# =============================================
# EMAIL CONFIGURATION
# =============================================

# SMTP Server Settings
SMTP_SERVER = "smtp.gmail.com"  # Gmail SMTP server
SMTP_PORT = 587  # TLS port

# Email Credentials
# For Gmail: Use App Password (https://myaccount.google.com/apppasswords)
SMTP_USER = "your-email@gmail.com"
SMTP_PASSWORD = "your-app-password"  # ⚠️ NEVER commit real passwords to git!

# Email Addresses
EMAIL_FROM = "globalmart-alerts@example.com"
EMAIL_TO = [
    "admin@example.com",
    "operations@example.com",
    "inventory@example.com"
]

# =============================================
# ALERT THRESHOLDS
# =============================================

# Inventory Alerts
LOW_STOCK_THRESHOLD = 10  # Alert when available stock < 10 units
CRITICAL_STOCK_THRESHOLD = 5  # Critical alert when < 5 units

# Anomaly Detection
ANOMALY_SCORE_THRESHOLD = 0.8  # Alert for anomaly scores >= 0.8
HIGH_RISK_THRESHOLD = 0.95  # Urgent alert for scores >= 0.95

# Cart Abandonment
CART_ABANDONMENT_HOURLY_LIMIT = 20  # Alert if > 20 carts abandoned per hour
CART_VALUE_THRESHOLD = 1000  # Alert for high-value abandoned carts (> $1000)

# =============================================
# MONITORING SETTINGS
# =============================================

# Check interval in seconds
CHECK_INTERVAL = 300  # 5 minutes (300 seconds)

# Alert deduplication window (seconds)
ALERT_DEDUP_WINDOW = 3600  # Don't send same alert within 1 hour

# Database connection pooling
DB_POOL_SIZE = 5
DB_MAX_OVERFLOW = 10

# =============================================
# NOTIFICATION CHANNELS
# =============================================

# Enable/disable notification channels
ENABLE_EMAIL = True
ENABLE_SLACK = False  # Future: Slack webhook integration
ENABLE_SMS = False  # Future: Twilio SMS integration
ENABLE_WEBHOOK = False  # Future: Custom webhook

# Slack configuration (if enabled)
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
SLACK_CHANNEL = "#globalmart-alerts"

# =============================================
# LOGGING
# =============================================

LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = "/tmp/globalmart_notifications.log"
LOG_MAX_BYTES = 10485760  # 10MB
LOG_BACKUP_COUNT = 5

# =============================================
# TESTING & DEVELOPMENT
# =============================================

# Set to True to enable test mode (no actual emails sent)
TEST_MODE = True  # ⚠️ Set to False in production

# Test mode: Print emails to console instead of sending
PRINT_EMAILS_TO_CONSOLE = True

# Test email recipient (for testing only)
TEST_EMAIL_TO = ["dev-test@example.com"]

# =============================================
# ALTERNATIVE SMTP PROVIDERS
# =============================================

# Uncomment and configure for your provider:

# # SendGrid
# SMTP_SERVER = "smtp.sendgrid.net"
# SMTP_PORT = 587
# SMTP_USER = "apikey"
# SMTP_PASSWORD = "your-sendgrid-api-key"

# # AWS SES
# SMTP_SERVER = "email-smtp.us-east-1.amazonaws.com"
# SMTP_PORT = 587
# SMTP_USER = "your-ses-smtp-username"
# SMTP_PASSWORD = "your-ses-smtp-password"

# # Mailgun
# SMTP_SERVER = "smtp.mailgun.org"
# SMTP_PORT = 587
# SMTP_USER = "postmaster@your-domain.mailgun.org"
# SMTP_PASSWORD = "your-mailgun-password"

# # Microsoft 365
# SMTP_SERVER = "smtp.office365.com"
# SMTP_PORT = 587
# SMTP_USER = "your-email@your-domain.com"
# SMTP_PASSWORD = "your-password"
