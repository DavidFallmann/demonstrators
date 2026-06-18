import json
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import SimpleTestCase

from common_models.common_models_app.models import MeteringPoint, UserProfile, TimeSeriesMeta, Consumption
from consumer.kafka_consumer.processing.json_processor import process_data_json

test_data_path = Path(__file__).parent / 'test_data'
USER_ID = 1


class KafkaConsumerTest(SimpleTestCase):
    databases = '__all__'

    def tearDown(self) -> None:
        pass # keep db after tests for debugging purposes

    @classmethod
    def tearDownClass(cls):
        pass # keep db after tests for debugging purposes

    def setUp(self):
        call_command('flush', '--no-input')
        User.objects.create(id=USER_ID, username='testuser', password='testpass', is_superuser=True, is_staff=True,
                            first_name='Test', last_name='User', email='test', is_active=True,
                            date_joined='2024-01-01T00:00:00Z')

    def test_process_valid_json(self):
        # given
        with open(test_data_path / 'valid.json') as file:
            data = json.load(file)
            create_user(data)
            given_points_list = (
                data['ValidatedHistoricalData_MarketDocument']
                ['TimeSeriesList']['TimeSeries'][0]['Series_PeriodList']
                ['Series_Period'][0]['PointList']['Point']
            )
            given_consumption_list = [point['energy_Quantity.quantity'] for point in given_points_list]

        # when
        process_data_json(data)

        # then
        self.assertEqual(MeteringPoint.objects.count(), 1)
        self.assertEqual(TimeSeriesMeta.objects.count(), 1)
        self.assertEqual(Consumption.objects.count(), len(given_consumption_list))

        time_series_meta = TimeSeriesMeta.objects.first()
        metering_point = MeteringPoint.objects.first()
        self.assertEqual(time_series_meta.metering_point_id, metering_point.id)
        for actual, given in zip(Consumption.objects.all(), given_consumption_list):
            self.assertEqual(time_series_meta.id, actual.time_series_meta_id)
            self.assertEqual(actual.consumption_value, given)



    def test_process_no_connection_id(self):
        # given
        with open(test_data_path / 'no_connection_id.json') as file:
            data = json.load(file)

        # when
        process_data_json(data)

        # then
        self.assertEqual(MeteringPoint.objects.count(), 0)

    def test_process_no_time_series_list(self):
        # given
        with open(test_data_path / 'no_time_series_list.json') as file:
            data = json.load(file)
            create_user(data)

        # when
        process_data_json(data)

        # then
        self.assertEqual(MeteringPoint.objects.count(), 0)


def create_user(data):
    connectionid = data['MessageDocumentHeader']['MessageDocumentHeader_MetaInformation']['connectionid']
    UserProfile.objects.create(user_id=USER_ID, connection_id=connectionid)
