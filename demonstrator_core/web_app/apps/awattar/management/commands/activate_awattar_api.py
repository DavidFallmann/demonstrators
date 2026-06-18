import logging.config

import requests
from django.core.management.base import BaseCommand

from web_app.apps.awattar.services.process_awattar_data import process_awattar_data
from web_app.core.settings import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    This command fetches data from the awattar API and saves it to the database.
    It is intended to be run as a scheduled task (e.g., via cron) to keep the market price data up to date.
    """
    help = 'Activates awattar API and save incoming data to DB'

    def handle(self, *args, **kwargs):
        awattar_response = _fetch_awattar_data()
        process_awattar_data(awattar_response)
        logger.info("Awattar API activated")


def _fetch_awattar_data():
    try:
        response = requests.get('https://api.awattar.de/v1/marketdata')
        return response.json()
    except Exception:
        logger.exception("Error fetching data from awattar API")
        return None
