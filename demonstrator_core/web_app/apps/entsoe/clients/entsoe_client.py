import logging.config
import os

import requests

from web_app.core.settings import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


def fetch_data_from_entsoe(zone, start_datetime, end_datetime, unit, metering_interval, consumption_data):
    url = os.environ.get("ENTSOE_API_URL")
    if url is None:
        raise ValueError("ENTSOE_API_URL environment variable not set.")

    headers = {"Content-Type": "application/json"}
    payload = {
        "zone": zone,
        "start": start_datetime.strftime("%Y%m%d%H%M"),
        "end": end_datetime.strftime("%Y%m%d%H%M"),
        "unit": unit,
        "resolution": metering_interval,
        "consumption": consumption_data
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        logger.error("The POST request to the ENTSOE microservice timed out.")
        return {}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending data ENTSOE to microservice: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error encountered: {e}")
        return {}