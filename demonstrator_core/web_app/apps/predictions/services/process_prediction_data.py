import logging.config
import logging.config
from datetime import datetime, timezone

import isodate

from common_models.common_models_app.models import (
    UserProfile, MeteringPoint, TimeSeriesMeta,
    Consumption, PredictionData
)
from web_app.apps.predictions.clients.predictions_client import fetch_data_from_predictions
from web_app.core.settings import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


def process_prediction_data(connection_id, start_dt, end_dt):
    logger.debug(f"Calculating Predictions (connection_id={connection_id}, start={start_dt}, end={end_dt})")

    users = __fetch_users(connection_id)
    for user in users:
        metering_points = MeteringPoint.objects.filter(user_profile=user)
        for mp in metering_points:
            time_series_metas = TimeSeriesMeta.objects.filter(metering_point=mp)
            for ts_meta in time_series_metas:

                consumption_qs = __fetch_consumption_data(end_dt, start_dt, ts_meta)
                if not consumption_qs.exists():
                    continue

                response = __fetch_data_from_predictions(consumption_qs, mp, ts_meta)
                if response:
                    logger.debug(f"Prediction response for user={user.user.username}, MP={mp.metering_point}")
                    __persist_prediction_data(ts_meta, response)
                else:
                    logger.debug(f"No prediction data returned for user: {user.user.username}, MP={mp.metering_point}")


def __fetch_users(connection_id):
    if not connection_id:
        logger.debug("Processing ALL users (no connection_id given).")
        return UserProfile.objects.all()
    try:
        logger.debug(f"Processing only user with ID={connection_id}")
        return [UserProfile.objects.get(connection_id=connection_id)]
    except UserProfile.DoesNotExist:
        logger.error(f"No UserProfile found for connection_id={connection_id}")
        return []

def __fetch_consumption_data(end_dt, start_dt, ts_meta):
    consumption_qs = Consumption.objects.filter(
        time_series_meta=ts_meta,
        timestamp__gte=start_dt,
        timestamp__lte=end_dt
    ).order_by('timestamp')
    return consumption_qs

def __fetch_data_from_predictions(consumption_qs, mp, ts_meta):
    consumption_data = list(consumption_qs.values_list('consumption_value', flat=True))
    zone = mp.metering_point[:2]
    unit = ts_meta.unit
    metering_interval = isodate.duration_isoformat(ts_meta.metering_interval)
    start_datetime = consumption_qs.first().timestamp
    end_datetime   = consumption_qs.last().timestamp

    return fetch_data_from_predictions(zone, start_datetime, end_datetime, unit, metering_interval, consumption_data)

def __persist_prediction_data(ts_meta, response):
    predictions_for_all_consumption_list = response["consumption"]["quarter_hourly"]
    next_day_total = response["consumption"]["total"]
    response_unit = response["unit"]

    for timestamp_str, value in predictions_for_all_consumption_list.items():
        timestamp_datetime = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        PredictionData.objects.get_or_create(
            time_series_meta=ts_meta,
            timestamp=timestamp_datetime,
            defaults={
                'prediction_value': value,
                'total_next_day': next_day_total,
                'unit': response_unit
            }
        )