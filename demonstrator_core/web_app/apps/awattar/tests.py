from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from django.core.management import call_command
from django.test import SimpleTestCase

from common_models.common_models_app.models import marketprice_data
from web_app.apps.awattar.services.process_awattar_data import process_awattar_data

test_data_path = Path(__file__).parent / 'test_data'


class AwattarTest(SimpleTestCase):
    databases = '__all__'

    def tearDown(self) -> None:
        pass # keep db after tests for debugging purposes

    @classmethod
    def tearDownClass(cls):
        pass # keep db after tests for debugging purposes

    def setUp(self):
        call_command('flush', '--no-input')

    def test_awattar_valid(self):
        # given
        given_start_time = datetime.now(tz=timezone.utc)
        given_end_time = datetime.now(tz=timezone.utc) + timedelta(hours=1)
        given_market_price = Decimal("123.45")
        given_unit = "Eur/MWh"
        given_data = {
            "start_timestamp": int(given_start_time.timestamp() * 1000),
            "end_timestamp": int(given_end_time.timestamp() * 1000),
            "marketprice": given_market_price,
            "unit": given_unit
        }

        # when
        process_awattar_data({
            "data": [given_data]
        })

        # then
        self.assertEqual(marketprice_data.objects.count(), 1)

        actual_market_price_data = marketprice_data.objects.first()
        self.assertEqual(actual_market_price_data.start_timestamp.replace(microsecond=0),
                         given_start_time.replace(microsecond=0))
        self.assertEqual(actual_market_price_data.end_timestamp.replace(microsecond=0),
                         given_end_time.replace(microsecond=0))
        self.assertEqual(actual_market_price_data.marketprice, given_market_price)
        self.assertEqual(actual_market_price_data.unit, given_unit)

    def test_awattar_invalid(self):
        # when
        process_awattar_data({})

        # then
        self.assertEqual(marketprice_data.objects.count(), 0)
