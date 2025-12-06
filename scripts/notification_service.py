#!/usr/bin/env python3
"""
GlobalMart Alert Notification System
Monitors database for critical events and sends notifications
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import time
import logging
import psycopg2
from typing import List, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"  # Change to your SMTP server
SMTP_PORT = 587
SMTP_USER = "your-email@gmail.com"  # Change to your email
SMTP_PASSWORD = "your-app-password"  # Change to your app password
EMAIL_FROM = "globalmart-alerts@example.com"
EMAIL_TO = ["admin@example.com", "operations@example.com"]  # Recipients

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'globalmart',
    'user': 'globalmart',
    'password': 'globalmart123'
}

# Alert thresholds
LOW_STOCK_THRESHOLD = 10  # Alert when stock below this
ANOMALY_SCORE_THRESHOLD = 0.8  # Alert for anomaly scores above this
CHECK_INTERVAL = 300  # Check every 5 minutes (300 seconds)

class NotificationService:
    def __init__(self):
        self.last_check_time = datetime.now() - timedelta(hours=1)
        self.sent_alerts = set()  # Track sent alerts to avoid duplicates

    def get_db_connection(self):
        """Get PostgreSQL connection"""
        return psycopg2.connect(**DB_CONFIG)

    def send_email(self, subject: str, body: str, recipients: List[str] = None):
        """Send email notification"""
        if recipients is None:
            recipients = EMAIL_TO

        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = EMAIL_FROM
            message["To"] = ", ".join(recipients)

            # Create HTML body
            html_body = f"""
            <html>
              <body style="font-family: Arial, sans-serif;">
                <div style="background-color: #f8f9fa; padding: 20px;">
                  <h2 style="color: #dc3545;">🚨 GlobalMart Alert</h2>
                  <div style="background-color: white; padding: 20px; border-radius: 5px;">
                    {body}
                  </div>
                  <p style="color: #6c757d; font-size: 12px; margin-top: 20px;">
                    This is an automated alert from GlobalMart Analytics Platform.<br>
                    Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                  </p>
                </div>
              </body>
            </html>
            """

            # Attach HTML
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)

            # Send email via SMTP
            # NOTE: For production, configure real SMTP credentials
            # For demo/testing, this will fail gracefully
            try:
                context = ssl.create_default_context()
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    server.starttls(context=context)
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.sendmail(EMAIL_FROM, recipients, message.as_string())

                logger.info(f"Email sent: {subject}")
                return True
            except Exception as smtp_error:
                # Log SMTP error but don't crash
                logger.warning(f"SMTP error (expected in demo): {smtp_error}")
                logger.info(f"Alert logged (would have sent): {subject}")
                return False

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    def check_low_stock_alerts(self):
        """Check for low stock items"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()

            query = """
                SELECT
                    product_id,
                    product_name,
                    category,
                    available_stock,
                    last_updated
                FROM inventory_status
                WHERE available_stock < %s
                    AND available_stock > 0
                ORDER BY available_stock ASC
                LIMIT 20
            """

            cur.execute(query, (LOW_STOCK_THRESHOLD,))
            results = cur.fetchall()

            if results:
                # Generate alert message
                items_html = "<h3>⚠️ Low Stock Alert</h3>"
                items_html += f"<p><strong>{len(results)} products</strong> are running low on stock:</p>"
                items_html += "<table border='1' cellpadding='8' style='border-collapse: collapse; width: 100%;'>"
                items_html += "<tr style='background-color: #f8f9fa;'><th>Product ID</th><th>Name</th><th>Category</th><th>Available</th></tr>"

                for row in results[:10]:  # Show top 10 in email
                    product_id, product_name, category, available_stock, last_updated = row
                    alert_key = f"low_stock_{product_id}_{available_stock}"

                    # Skip if already sent recently
                    if alert_key in self.sent_alerts:
                        continue

                    color = "#dc3545" if available_stock < 5 else "#ffc107"
                    items_html += f"""
                    <tr>
                        <td>{product_id}</td>
                        <td>{product_name or 'N/A'}</td>
                        <td>{category or 'N/A'}</td>
                        <td style='color: {color}; font-weight: bold;'>{available_stock} units</td>
                    </tr>
                    """

                    self.sent_alerts.add(alert_key)

                items_html += "</table>"

                if len(results) > 10:
                    items_html += f"<p><em>...and {len(results) - 10} more items</em></p>"

                items_html += "<p style='margin-top: 20px;'><strong>Action Required:</strong> Please restock these items to avoid stockouts.</p>"

                # Send notification
                self.send_email(
                    f"🚨 Low Stock Alert - {len(results)} Products Below Threshold",
                    items_html
                )

            cur.close()
            conn.close()

        except Exception as e:
            logger.error(f"Error checking low stock: {e}")

    def check_transaction_anomalies(self):
        """Check for high-risk transaction anomalies"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()

            # Check for anomalies since last check
            query = """
                SELECT
                    transaction_id,
                    user_id,
                    amount,
                    anomaly_score,
                    anomaly_type,
                    detected_at,
                    description
                FROM transaction_anomalies
                WHERE detected_at >= %s
                    AND anomaly_score >= %s
                ORDER BY anomaly_score DESC
                LIMIT 20
            """

            cur.execute(query, (self.last_check_time, ANOMALY_SCORE_THRESHOLD))
            results = cur.fetchall()

            if results:
                # Generate alert message
                anomalies_html = "<h3>🚨 Transaction Anomaly Alert</h3>"
                anomalies_html += f"<p><strong>{len(results)} high-risk transactions</strong> detected:</p>"
                anomalies_html += "<table border='1' cellpadding='8' style='border-collapse: collapse; width: 100%;'>"
                anomalies_html += "<tr style='background-color: #f8f9fa;'><th>Transaction ID</th><th>User ID</th><th>Amount</th><th>Score</th><th>Type</th></tr>"

                for row in results[:10]:
                    transaction_id, user_id, amount, anomaly_score, anomaly_type, detected_at, description = row
                    alert_key = f"anomaly_{transaction_id}"

                    # Skip if already sent
                    if alert_key in self.sent_alerts:
                        continue

                    score_color = "#dc3545" if anomaly_score >= 0.9 else "#ffc107"
                    anomalies_html += f"""
                    <tr>
                        <td>{transaction_id}</td>
                        <td>{user_id}</td>
                        <td>${float(amount):,.2f}</td>
                        <td style='color: {score_color}; font-weight: bold;'>{float(anomaly_score):.2f}</td>
                        <td>{anomaly_type}</td>
                    </tr>
                    """

                    self.sent_alerts.add(alert_key)

                anomalies_html += "</table>"

                if len(results) > 10:
                    anomalies_html += f"<p><em>...and {len(results) - 10} more anomalies</em></p>"

                anomalies_html += "<p style='margin-top: 20px;'><strong>Action Required:</strong> Review these transactions for potential fraud.</p>"

                # Send notification
                self.send_email(
                    f"🚨 Anomaly Alert - {len(results)} High-Risk Transactions",
                    anomalies_html
                )

            cur.close()
            conn.close()

        except Exception as e:
            logger.error(f"Error checking anomalies: {e}")

    def check_cart_abandonment(self):
        """Check for recent cart abandonment events"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()

            # Get cart abandonments from last hour
            query = """
                SELECT COUNT(*) as count,
                       COALESCE(SUM(cart_value), 0) as total_value
                FROM cart_abandonment
                WHERE abandonment_time >= %s
            """

            one_hour_ago = datetime.now() - timedelta(hours=1)
            cur.execute(query, (one_hour_ago,))
            result = cur.fetchone()

            if result and result[0] > 20:  # Alert if more than 20 abandonments in 1 hour
                count, total_value = result

                alert_html = f"""
                <h3>🛒 Cart Abandonment Alert</h3>
                <p><strong>{count} shopping carts</strong> abandoned in the last hour</p>
                <p><strong>Total Potential Revenue Lost:</strong> ${float(total_value):,.2f}</p>
                <p style='margin-top: 20px;'><strong>Recommendation:</strong> Consider:
                <ul>
                    <li>Sending reminder emails to customers</li>
                    <li>Offering limited-time discounts</li>
                    <li>Reviewing checkout process for issues</li>
                </ul>
                </p>
                """

                self.send_email(
                    f"🛒 Cart Abandonment Spike - {count} Carts in Last Hour",
                    alert_html
                )

            cur.close()
            conn.close()

        except Exception as e:
            logger.error(f"Error checking cart abandonment: {e}")

    def run(self):
        """Main monitoring loop"""
        logger.info("=" * 70)
        logger.info("GlobalMart Notification Service Started")
        logger.info("=" * 70)
        logger.info(f"Monitoring interval: {CHECK_INTERVAL} seconds")
        logger.info(f"Low stock threshold: {LOW_STOCK_THRESHOLD} units")
        logger.info(f"Anomaly score threshold: {ANOMALY_SCORE_THRESHOLD}")
        logger.info(f"Email recipients: {', '.join(EMAIL_TO)}")
        logger.info("=" * 70)
        logger.info("")

        while True:
            try:
                logger.info(f"Running checks at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                # Run all checks
                self.check_low_stock_alerts()
                self.check_transaction_anomalies()
                self.check_cart_abandonment()

                # Update last check time
                self.last_check_time = datetime.now()

                # Clear old alerts (keep last 1000)
                if len(self.sent_alerts) > 1000:
                    self.sent_alerts = set(list(self.sent_alerts)[-1000:])

                logger.info(f"Checks complete. Next check in {CHECK_INTERVAL} seconds.")
                logger.info("")

                # Sleep until next check
                time.sleep(CHECK_INTERVAL)

            except KeyboardInterrupt:
                logger.info("\nShutting down notification service...")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)  # Wait 30s before retrying

if __name__ == "__main__":
    service = NotificationService()
    service.run()
