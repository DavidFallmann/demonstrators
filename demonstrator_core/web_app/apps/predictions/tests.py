import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, Mock

import isodate
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import SimpleTestCase

from common_models.common_models_app.models import UserProfile, MeteringPoint, TimeSeriesMeta, \
    Consumption, PredictionData
from web_app.apps.predictions.services.assemble_prediction_data import assemble_prediction_data
from web_app.apps.predictions.services.process_prediction_data import process_prediction_data


class PredictionsTest(SimpleTestCase):
    databases = '__all__'

    def tearDown(self) -> None:
        pass # keep db after tests for debugging purposes

    @classmethod
    def tearDownClass(cls):
        pass # keep db after tests for debugging purposes

    def setUp(self):
        call_command('flush', '--no-input')

    def test_assemble_prediction_data_success(self):
        # given
        user, user_profile = _setup_user()
        metering_points = _setup_metering_points(user_profile)
        time_series_metas = _setup_time_series_metas(metering_points)
        prediction_data = _setup_prediction_data(time_series_metas)
        _setup_consumption_data(time_series_metas)

        # when
        request = Mock()
        request.user = user
        actual_prediction_data = assemble_prediction_data(request)

        # then
        expected_prediction_data = {}
        for time_series_meta, predictions in prediction_data.items():
            for prediction in predictions:
                key = time_series_meta.metering_point.metering_point
                if key not in expected_prediction_data:
                    expected_prediction_data[key] = []
                expected_prediction_data[key].append({
                    'timestamp': prediction.timestamp,
                    'prediction_value': prediction.prediction_value,
                })
        expected_predictions_start_end = {
            time_series_meta.metering_point.metering_point: {
                'start': predictions[0].timestamp,
                'end': predictions[-1].timestamp,
            } for time_series_meta, predictions in prediction_data.items()
        }
        expected_predicted_consumption_tomorrow = sum(
            prediction.prediction_value
            for prediction in next(reversed(prediction_data.values()))
        )
        self.assertEqual(actual_prediction_data['prediction_data'], expected_prediction_data)
        self.assertEqual(actual_prediction_data['prediction_start_end'], expected_predictions_start_end)
        self.assertEqual(actual_prediction_data['predicted_consumption_tomorrow'], expected_predicted_consumption_tomorrow)

    def test_assemble_prediction_data_no_conumption(self):
        # given
        user, user_profile = _setup_user()
        _setup_metering_points(user_profile)

        # when
        request = Mock()
        request.user = user
        actual_prediction_data = assemble_prediction_data(request)

        # then
        self.assertEqual(actual_prediction_data['prediction_data'], {})
        self.assertEqual(actual_prediction_data['prediction_start_end'], {})
        self.assertEqual(actual_prediction_data['predicted_consumption_tomorrow'], 0.0)

    def test_process_prediction_data_success(self):
        _, user_profile = _setup_user()
        metering_points = _setup_metering_points(user_profile)
        time_series_metas = _setup_time_series_metas(metering_points)
        consumption_data = _setup_consumption_data(time_series_metas)
        given_zone = metering_points[0].metering_point[:2]
        given_unit = time_series_metas[0].unit
        given_metering_interval = isodate.duration_isoformat(time_series_metas[0].metering_interval)
        start_time = consumption_data[0].timestamp
        end_time = consumption_data[-1].timestamp
        given_consumption_data = {
            'quarter_hourly': {consumption.timestamp.strftime("%Y-%m-%d %H:%M:%S"): consumption.consumption_value for
                               consumption in consumption_data},
            'total': 10.0
        }
        resolution = "PT15M"

        with patch(
                'web_app.apps.predictions.services.process_prediction_data.fetch_data_from_predictions') as mock_send:
            mock_send.return_value = {
                'start': start_time.strftime('%Y%m%d%H%M'),
                'unit': given_unit,
                'resolution': resolution,
                'consumption': given_consumption_data,
            }
            process_prediction_data(user_profile.connection_id, str(start_time), str(end_time))

            mock_send.assert_called_once_with(given_zone, start_time, end_time, given_unit,
                                              given_metering_interval,
                                              [consumption.consumption_value for consumption in consumption_data])
            self.assertEqual(PredictionData.objects.count(), 2)
            for idx, prediction in enumerate(PredictionData.objects.all()):
                self.assertEqual(prediction.time_series_meta, time_series_metas[0])
                self.assertEqual(prediction.timestamp, consumption_data[idx].timestamp.replace(microsecond=0))
                self.assertEqual(prediction.prediction_value, consumption_data[idx].consumption_value)
                self.assertEqual(prediction.unit, given_unit)


def _setup_user():
    return (User.objects.create(id=1, username='testuser', password='testpass', is_superuser=True, is_staff=True,
                                first_name='Test', last_name='User', email='test', is_active=True,
                                date_joined='2024-01-01T00:00:00Z'),
            UserProfile.objects.create(user_id=1, connection_id=str(uuid.uuid4())))


def _setup_metering_points(user_profile):
    return [MeteringPoint.objects.create(user_profile=user_profile, connection_id=user_profile.connection_id,
                                         data_need_id=str(uuid.uuid4()), permission_id=str(uuid.uuid4()),
                                         metering_point='test_metering_point')]


def _setup_time_series_metas(metering_points):
    return [TimeSeriesMeta.objects.create(metering_point=metering_point, start_datetime=datetime.now(tz=timezone.utc),
                                          metering_interval=timedelta(minutes=15), unit='kWh')
            for metering_point in metering_points]


def _setup_consumption_data(time_series_metas):
    return [
        Consumption.objects.create(time_series_meta=time_series_meta,
                                   timestamp=datetime.now(tz=timezone.utc) + timedelta(minutes=i),
                                   consumption_value=10.0) for i in range(2)
        for time_series_meta in time_series_metas]


def _setup_prediction_data(time_series_metas):
    predictions_per_time_series = {}
    for time_series_meta in time_series_metas:
        predictions_per_time_series[time_series_meta] = [
            PredictionData.objects.create(time_series_meta=time_series_meta,
                                          timestamp=datetime.now(tz=timezone.utc) + timedelta(minutes=i + 5),
                                          # timestamps need to be unique and need to be after the last consumption timestamp to not trigger an api call
                                          prediction_value=10.0, total_next_day=10.0)
            for i in range(24 * 4)]  # 24 hours with 15-minute intervals
    return predictions_per_time_series
