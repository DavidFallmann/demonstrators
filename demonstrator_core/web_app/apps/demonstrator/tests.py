from datetime import datetime
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.test import SimpleTestCase

from web_app.apps.demonstrator.services.compare_prices import compare_prices


class ComparePricesTest(SimpleTestCase):
    databases = '__all__'

    def tearDown(self) -> None:
        pass # keep db after tests for debugging purposes

    @classmethod
    def tearDownClass(cls):
        pass # keep db after tests for debugging purposes

    def setUp(self):
        call_command('flush', '--no-input')

    def test_compare_prices(self):
        with patch('web_app.apps.demonstrator.services.compare_prices.fetch_awattar_data') as mock_awattar, \
                patch('web_app.apps.demonstrator.services.compare_prices.assemble_prediction_data') as mock_predictions, \
                patch('web_app.apps.demonstrator.services.compare_prices.tariff_form') as mock_tariff_form:

            mock_awattar.return_value = {
                'next_24h_data': [{'marketprice': '0.15'}],
            }
            mock_predictions.return_value = {
                'prediction_data': {'test_metering_point': [{'timestamp': datetime.fromisoformat('2026-04-17T11:32:30.708Z'), 'prediction_value': 10.0}]}
            }

            mock_form = Mock()
            mock_form.is_valid.return_value = True
            mock_form.cleaned_data = {'fixed_tariff': 0.20}
            mock_tariff_form.return_value = mock_form

            request = Mock()
            request.method = 'POST'

            # when
            actual_context = compare_prices(request)

            # then
            self.assertIsNotNone(actual_context)
            self.assertEqual(actual_context['cost_graph_data'], '[{"timestamp": "2026-04-17T11:32:30.708000+00:00", "dynamic_cost": 0.0014999999999999998, "fixed_cost": 0.002}]')
