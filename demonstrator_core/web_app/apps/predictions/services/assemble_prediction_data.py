import logging.config
from datetime import timedelta

from common_models.common_models_app.models import MeteringPoint, Consumption, UserProfile, PredictionData
from web_app.apps.predictions.services.process_prediction_data import process_prediction_data
from web_app.core.settings import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


def assemble_prediction_data(request):
    prediction_data = {}
    prediction_start_end = {}
    total_prediction_tomorrow = 0.0
    user_profile = UserProfile.objects.get(user=request.user)
    metering_points = MeteringPoint.objects.filter(user_profile=user_profile)

    for metering_point in metering_points:
        prediction_qs = __update_predictions(metering_point, user_profile)
        if not prediction_qs.exists():
            continue

        prediction_data[metering_point.metering_point] = list(
            prediction_qs.values('timestamp', 'prediction_value')
        )
        prediction_start_end[metering_point.metering_point] = {
            'start': prediction_qs.first().timestamp,
            'end': prediction_qs.last().timestamp,
        }
        total_prediction_tomorrow = sum(
            p['prediction_value'] for p in prediction_data[metering_point.metering_point]
        )

    return {
        'prediction_data': prediction_data,
        'prediction_start_end': prediction_start_end,
        'predicted_consumption_tomorrow': round(total_prediction_tomorrow, 3),
    }


def __update_predictions(metering_point, user_profile):
    consumption_qs = __fetch_consumption(metering_point)
    if not consumption_qs.exists():
        logger.info("No consumption data found for metering_point: %s", metering_point.metering_point)
        return consumption_qs

    earliest_timestamp_consumption = consumption_qs.first().timestamp

    prediction_begin = consumption_qs.last().timestamp
    prediction_end = prediction_begin + timedelta(hours=24)
    prediction_qs = __fetch_predictions(metering_point, prediction_begin, prediction_end)

    expected = __calculate_expected_prediction_count(consumption_qs, prediction_begin, prediction_end)
    have = prediction_qs.count()

    if have < expected:
        process_prediction_data(
            user_profile.connection_id, earliest_timestamp_consumption.isoformat(), prediction_begin.isoformat()
        )
        prediction_qs = __fetch_predictions(metering_point, prediction_begin, prediction_end)

    logger.info("prediction_qs have=%s expected=%s (metering_point=%s)", have, expected, metering_point.metering_point)
    return prediction_qs


def __calculate_expected_prediction_count(consumption_qs, prediction_begin, prediction_end):
    ts_meta = consumption_qs.first().time_series_meta
    resolution = getattr(ts_meta, "metering_interval", None) or timedelta(minutes=15)
    return int((prediction_end - prediction_begin) // resolution)


def __fetch_consumption(metering_point):
    return (
        Consumption.objects
        .filter(time_series_meta__metering_point=metering_point)
        .order_by('timestamp')
    )


def __fetch_predictions(metering_point, prediction_begin, prediction_end):
    return PredictionData.objects.filter(
        time_series_meta__metering_point=metering_point,
        timestamp__gte=prediction_begin,
        timestamp__lt=prediction_end
    ).order_by('timestamp')
