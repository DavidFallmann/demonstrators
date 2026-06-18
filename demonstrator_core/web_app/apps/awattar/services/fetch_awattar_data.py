import logging.config
from datetime import timedelta

from django.utils import timezone

from common_models.common_models_app.models import marketprice_data
from web_app.core.settings import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


def fetch_awattar_data():
    # Query the full local calendar day (00:00–23:59 local time).
    # Since Django uses UTC internally, we add a ±3h buffer to cover
    # any UTC offset (e.g. UTC+2 for Austria) so the frontend can
    # filter to the exact local midnight–midnight window.
    today_utc_midnight = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    awattar_begin = today_utc_midnight - timedelta(hours=3)
    awattar_end   = today_utc_midnight + timedelta(hours=27)
    awattar_qs = marketprice_data.objects.filter(
        start_timestamp__gte=awattar_begin,
        start_timestamp__lt=awattar_end
    ).order_by('start_timestamp')

    if awattar_qs.exists():
        return {
            'next_24h_data': list(awattar_qs.values())
        }
    else:
        logger.info("No aWATTar data available")
        return {
            'next_24h_data': []
        }
