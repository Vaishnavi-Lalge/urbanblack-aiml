import logging
from datetime import datetime
import pytz

# ✅ IST timezone
IST = pytz.timezone("Asia/Kolkata")


class ISTFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, IST)
        return dt.strftime("%Y-%m-%d %H:%M:%S IST")


def get_logger(name: str):
    logger = logging.getLogger(name)

    if not logger.handlers:  # prevent duplicate logs
        logger.setLevel(logging.INFO)

        console_handler = logging.StreamHandler()

        formatter = ISTFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger