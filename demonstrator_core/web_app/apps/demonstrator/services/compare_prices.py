import json
import logging.config

from web_app.apps.awattar.services.fetch_awattar_data import fetch_awattar_data
from web_app.apps.demonstrator.forms import tariff_form
from web_app.apps.predictions.services.assemble_prediction_data import assemble_prediction_data
from web_app.core.settings import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


def compare_prices(request):
    form = tariff_form()
    context = {'form': form}
    if request.method != "POST":
        return context

    form = tariff_form(request.POST)
    if not form.is_valid():
        context['error'] = "Invalid input. Please try again."
        return context

    fixed_tariff = form.cleaned_data['fixed_tariff']  # €/MWh
    awattar_raw = fetch_awattar_data()['next_24h_data']
    pred_raw = assemble_prediction_data(request)['prediction_data']

    if not pred_raw:
        context['error'] = "No prediction data available."
        return context

    predictions = get_predictions(pred_raw)
    quarter_prices = calculate_quarter_prices(awattar_raw, predictions)
    cost_graph = calculate_cost_graph_data(fixed_tariff, predictions, quarter_prices[:len(predictions)])

    context.update({
        'cost_graph_data': json.dumps(cost_graph),
        'success': 'true',
    })
    return context


def get_predictions(pred_raw):
    first_mp = next(iter(pred_raw))
    predictions = sorted(pred_raw[first_mp], key=lambda p: p['timestamp'])
    return predictions


def calculate_quarter_prices(awattar_raw, predictions):
    quarter_prices = []
    for rec in awattar_raw:
        price_kwh = float(rec['marketprice']) / 1000.0
        quarter_prices.extend([price_kwh] * 4)

    if len(quarter_prices) < len(predictions):
        missing = len(predictions) - len(quarter_prices)
        quarter_prices.extend([0.0] * missing)
        logger.info(
            "aWATTar delivered only %s of %s quarter-hours – "
            "missing slots set to €0.00.",
            len(quarter_prices) - missing, len(predictions)
        )
    return quarter_prices


def calculate_cost_graph_data(fixed_tariff, predictions, quarter_prices):
    fixed_per_kwh = fixed_tariff / 1000.0
    cost_graph = []

    for idx, pred in enumerate(predictions):
        kwh = pred['prediction_value']
        price = quarter_prices[idx]

        dyn = kwh * price
        fix = kwh * fixed_per_kwh

        cost_graph.append({
            'timestamp': pred['timestamp'].isoformat(),
            'dynamic_cost': dyn,
            'fixed_cost': fix,
        })

    return cost_graph
