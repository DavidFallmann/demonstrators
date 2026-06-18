from datetime import datetime, timezone
from decimal import Decimal

from django.db import transaction

from common_models.common_models_app.models import marketprice_data


def process_awattar_data(awattar_response):
    data = awattar_response.get('data') or []
    with transaction.atomic():
        for item in data:
            start_timestamp_seconds = item['start_timestamp'] / 1000
            end_timestamp_seconds = item['end_timestamp'] / 1000
            marketprice = Decimal(item['marketprice'])
            unit = item['unit']

            start_timestamp = datetime.fromtimestamp(start_timestamp_seconds, tz=timezone.utc)
            end_timestamp = datetime.fromtimestamp(end_timestamp_seconds, tz=timezone.utc)

            marketprice_data.objects.get_or_create(
                start_timestamp=start_timestamp,
                defaults={
                    'end_timestamp': end_timestamp,
                    'marketprice': marketprice,
                    'unit': unit
                }
            )
