import logging
import os

import requests

from web_app.core.settings import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

def fetch_data_from_predictions(zone, start_datetime, end_datetime, unit, metering_interval, consumption_data):
    url = os.environ.get("PREDICTION_API_URL")

    headers = { "Content-Type": "application/json" }
    logger.debug(f"Calling prediction with zone = {zone}")
    payload = {
        "zone":       zone,
        "start":      start_datetime.strftime("%Y%m%d%H%M"),
        "end":        end_datetime.strftime("%Y%m%d%H%M"),
        "unit":       unit,
        "resolution": metering_interval,
        "consumption": consumption_data
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logger.error("The request to the Prediction microservice timed out.")
        return {}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending data to Prediction microservice: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error encountered: {e}")
        return {}
