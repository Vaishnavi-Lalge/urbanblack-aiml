import schedule
import time
from datetime import datetime
from config.settings import IST

from pipelines.daily_pipeline import run_pipeline
from utils.logger import get_logger

logger = get_logger(__name__)


# ---------------- JOB FUNCTION ----------------
def job():
    try:
        start_time = datetime.now(IST)
        logger.info(f"🔄 Daily ML pipeline triggered at {start_time.strftime('%Y-%m-%d %H:%M:%S IST')}")

        run_pipeline()

        end_time = datetime.now(IST)
        duration = (end_time - start_time).seconds

        logger.info(f"✅ Pipeline completed at {end_time.strftime('%Y-%m-%d %H:%M:%S IST')}")
        logger.info(f"⏱ Duration: {duration} seconds")

    except Exception as e:
        logger.error(f"❌ Pipeline failed: {str(e)}", exc_info=True)


# ---------------- SCHEDULER SETUP ----------------
schedule.every().day.at("02:00").do(job)

logger.info("⏰ Scheduler started (IST)... Waiting for next run...")


# ---------------- RUN LOOP ----------------
while True:
    try:
        schedule.run_pending()

        # Optional: log next run time (every minute)
        next_run = schedule.next_run()
        if next_run:
            next_run_ist = next_run.astimezone(IST)
            logger.debug(f"⏭ Next run at {next_run_ist.strftime('%Y-%m-%d %H:%M:%S IST')}")

        time.sleep(60)

    except KeyboardInterrupt:
        logger.info("🛑 Scheduler stopped manually")
        break

    except Exception as e:
        logger.error(f"❌ Scheduler error: {str(e)}", exc_info=True)
        time.sleep(60)