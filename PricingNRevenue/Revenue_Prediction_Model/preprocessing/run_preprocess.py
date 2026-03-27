import os

from ingestion.data_loader import load_data
from preprocessing.preprocess import preprocess_data
from utils.logger import get_logger

logger = get_logger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "processed", "processed_data.csv")


def run_preprocessing():
    try:
        logger.info("🚀 Starting preprocessing pipeline...")

        # Step 1: Load raw data
        logger.info("📥 Loading raw data...")
        df = load_data()

        if df is None or df.empty:
            raise ValueError("❌ Loaded dataset is empty!")

        logger.info(f"✅ Data loaded successfully. Shape: {df.shape}")

        # Step 2: Preprocess data
        logger.info("🧠 Running preprocessing...")
        processed_df = preprocess_data(df)

        if processed_df is None or processed_df.empty:
            raise ValueError("❌ Processed dataset is empty!")

        logger.info(f"✅ Preprocessing completed. Shape: {processed_df.shape}")

        # Step 3: Save processed data (redundant safety)
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        processed_df.to_csv(OUTPUT_PATH, index=False)

        logger.info(f"💾 Processed data saved at: {OUTPUT_PATH}")

        return processed_df

    except Exception as e:
        logger.error(f"❌ Preprocessing failed: {str(e)}")
        raise


if __name__ == "__main__":
    run_preprocessing()