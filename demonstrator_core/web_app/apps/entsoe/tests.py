import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, Mock

import isodate
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import SimpleTestCase

from common_models.common_models_app.models import UserProfile, MeteringPoint, TimeSeriesMeta, \
    Consumption, EmissionData
from web_app.apps.entsoe.services.assemble_emission_data import assemble_emission_data
from web_app.apps.entsoe.services.process_entsoe_data import process_entsoe_data


class EntsoeTest(SimpleTestCase):
    databases = '__all__'

    def tearDown(self) -> None:
        pass # keep db after tests for debugging purposes

    @classmethod
    def tearDownClass(cls):
        pass # keep db after tests for debugging purposes

    def setUp(self):
        call_command('flush', '--no-input')

    def test_assemble_emission_data_success(self):
        # given
        user, user_profile = _setup_user()
        metering_points = _setup_metering_points(user_profile)
        time_series_metas = _setup_time_series_metas(metering_points)
        consumption_data = _setup_consumption_data(time_series_metas)
        emission_data = setup_emission_data(consumption_data, time_series_metas)

        # when
        request = Mock()
        request.user = user
        actual_emission_data = assemble_emission_data(request)

        # then
        expected_emission_data = {
            emission.time_series_meta.metering_point.metering_point: [{
                'timestamp': emission.timestamp,
                'emission_value': emission.emission_value
            }] for emission in emission_data
        }
        expected_emission_start_end = {
            emission.time_series_meta.metering_point.metering_point: {
                'start': emission.timestamp,
                'end': emission.timestamp,
            } for emission in emission_data
        }
        self.assertEqual(actual_emission_data['emission_data'], expected_emission_data)
        self.assertEqual(actual_emission_data['emission_start_end'], expected_emission_start_end)

    def test_assemble_emission_data_no_consumption(self):
        # given
        user, user_profile = _setup_user()
        _setup_metering_points(user_profile)

        # when
        request = Mock()
        request.user = user
        actual_emission_data = assemble_emission_data(request)

        # then
        self.assertEqual(actual_emission_data['emission_data'], {})
        self.assertEqual(actual_emission_data['emission_start_end'], {})


    def test_process_entsoe_data_success(self):
        _, user_profile = _setup_user()
        metering_points = _setup_metering_points(user_profile)
        time_series_metas = _setup_time_series_metas(metering_points)
        consumption_data = _setup_consumption_data(time_series_metas)
        given_zone = metering_points[0].metering_point[:2]
        given_unit = time_series_metas[0].unit
        given_metering_interval = isodate.duration_isoformat(time_series_metas[0].metering_interval)
        start_time = consumption_data[0].timestamp
        end_time = consumption_data[-1].timestamp
        given_consumption_data = [consumption.consumption_value for consumption in consumption_data]
        resolution = "PT15M"

        with patch(
                'web_app.apps.entsoe.services.process_entsoe_data.fetch_data_from_entsoe') as mock_send:
            mock_send.return_value = {
                "start": start_time.strftime("%Y%m%d%H%M"),
                "unit": given_unit,
                "resolution": resolution,
                "consumption": given_consumption_data,
            }
            process_entsoe_data(user_profile.connection_id, str(start_time), str(end_time))

            mock_send.assert_called_once_with(given_zone, start_time, end_time, given_unit,
                                              given_metering_interval, given_consumption_data)
            self.assertEqual(EmissionData.objects.count(), 2)
            for idx, emission in enumerate(EmissionData.objects.all()):
                self.assertEqual(emission.time_series_meta, time_series_metas[0])
                self.assertEqual(emission.timestamp, start_time.replace(second=0, microsecond=0) + (
                            idx * isodate.parse_duration(resolution)))
                self.assertEqual(emission.emission_value, given_consumption_data[idx])
                self.assertEqual(emission.unit, given_unit)


def _setup_user():
    return (User.objects.create(id=1, username='testuser', password='testpass', is_superuser=True, is_staff=True,
                                first_name='Test', last_name='User', email='test', is_active=True,
                                date_joined='2024-01-01T00:00:00Z'),
            UserProfile.objects.create(user_id=1, connection_id=str(uuid.uuid4())))


def _setup_metering_points(user_profile):
    return [MeteringPoint.objects.create(user_profile=user_profile, connection_id=user_profile.connection_id,
                                         data_need_id=str(uuid.uuid4()), permission_id=str(uuid.uuid4()),
                                         metering_point='AT_test_metering_point')]


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

def setup_emission_data(consumption_data, time_series_metas):
        return [EmissionData.objects.create(time_series_meta=time_series_meta,
                                     timestamp=consumption_data[-1].timestamp + timedelta(minutes=1),
                                     emission_value=0.5)
                for time_series_meta in time_series_metas]
