from datetime import datetime
from config.settings import IST

from preprocessing.run_preprocess import run_preprocessing
from training.train import main as train_models
from utils.logger import get_logger

logger = get_logger(__name__)


def run_pipeline():
    pipeline_start = datetime.now(IST)

    try:
        logger.info("🚀 Starting Daily ML Pipeline")

        # ---------------- STEP 1: PREPROCESSING ----------------
        step_start = datetime.now(IST)
        logger.info("📊 Step 1: Preprocessing started")

        run_preprocessing()

        step_end = datetime.now(IST)
        logger.info(
            f"✅ Preprocessing completed in {(step_end - step_start).seconds} sec"
        )

        # ---------------- STEP 2: TRAINING ----------------
        step_start = datetime.now(IST)
        logger.info("🧠 Step 2: Model Training started")

        train_models()

        step_end = datetime.now(IST)
        logger.info(
            f"✅ Training completed in {(step_end - step_start).seconds} sec"
        )

        # ---------------- PIPELINE SUCCESS ----------------
        pipeline_end = datetime.now(IST)
        total_time = (pipeline_end - pipeline_start).seconds

        logger.info(
            f"🎉 Pipeline completed successfully in {total_time} sec"
        )

    except Exception as e:
        logger.error(f"❌ Pipeline failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    logger.info(
        f"📅 Pipeline triggered at {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')}"
    )
    run_pipeline()