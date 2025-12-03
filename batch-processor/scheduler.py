"""
Batch Job Scheduler for GlobalMart
Orchestrates all batch processing jobs
"""

import schedule
import time
import subprocess
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/logs/batch_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_etl():
    """Run ETL pipeline"""
    logger.info("Starting ETL Pipeline...")
    try:
        result = subprocess.run(
            ['python', 'etl_pipeline.py'],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        if result.returncode == 0:
            logger.info("ETL Pipeline completed successfully")
        else:
            logger.error(f"ETL Pipeline failed: {result.stderr}")
    except Exception as e:
        logger.error(f"Error running ETL Pipeline: {e}")

def run_rfm_analysis():
    """Run RFM Analysis"""
    logger.info("Starting RFM Analysis...")
    try:
        result = subprocess.run(
            ['python', 'rfm_analysis.py'],
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes timeout
        )
        if result.returncode == 0:
            logger.info("RFM Analysis completed successfully")
        else:
            logger.error(f"RFM Analysis failed: {result.stderr}")
    except Exception as e:
        logger.error(f"Error running RFM Analysis: {e}")

def run_product_performance():
    """Run Product Performance Analysis"""
    logger.info("Starting Product Performance Analysis...")
    try:
        result = subprocess.run(
            ['python', 'product_performance.py'],
            capture_output=True,
            text=True,
            timeout=1800
        )
        if result.returncode == 0:
            logger.info("Product Performance Analysis completed successfully")
        else:
            logger.error(f"Product Performance Analysis failed: {result.stderr}")
    except Exception as e:
        logger.error(f"Error running Product Performance Analysis: {e}")

def run_sales_trends():
    """Run Sales Trends Analysis"""
    logger.info("Starting Sales Trends Analysis...")
    try:
        result = subprocess.run(
            ['python', 'sales_trends.py'],
            capture_output=True,
            text=True,
            timeout=1800
        )
        if result.returncode == 0:
            logger.info("Sales Trends Analysis completed successfully")
        else:
            logger.error(f"Sales Trends Analysis failed: {result.stderr}")
    except Exception as e:
        logger.error(f"Error running Sales Trends Analysis: {e}")

def run_all_jobs():
    """Run all batch jobs in sequence"""
    logger.info("=" * 60)
    logger.info("Running all batch jobs...")
    logger.info("=" * 60)

    run_etl()
    run_rfm_analysis()
    run_product_performance()
    run_sales_trends()

    logger.info("=" * 60)
    logger.info("All batch jobs completed!")
    logger.info("=" * 60)

def setup_schedule():
    """Setup job schedule"""
    # Run ETL every 6 hours
    schedule.every(6).hours.do(run_etl)

    # Run RFM analysis daily at 2 AM
    schedule.every().day.at("02:00").do(run_rfm_analysis)

    # Run product performance analysis daily at 3 AM
    schedule.every().day.at("03:00").do(run_product_performance)

    # Run sales trends analysis daily at 4 AM
    schedule.every().day.at("04:00").do(run_sales_trends)

    logger.info("Job schedule configured:")
    logger.info("  - ETL Pipeline: Every 6 hours")
    logger.info("  - RFM Analysis: Daily at 2:00 AM")
    logger.info("  - Product Performance: Daily at 3:00 AM")
    logger.info("  - Sales Trends: Daily at 4:00 AM")

def start_scheduler():
    """Start the scheduler"""
    logger.info("Starting Batch Job Scheduler...")
    setup_schedule()

    # Run all jobs once at startup
    logger.info("Running initial batch jobs...")
    run_all_jobs()

    # Keep running scheduled jobs
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    start_scheduler()
