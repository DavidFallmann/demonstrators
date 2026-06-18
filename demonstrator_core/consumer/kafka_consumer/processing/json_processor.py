import logging.config

import isodate
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from django.db import transaction

from common_models.common_models_app.models import UserProfile, MeteringPoint, TimeSeriesMeta, Consumption
from web_app.core.settings import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

def _get_nested(d, *keys, label="field"):
    """Safely traverse nested dicts/lists. Raises ValueError with context on failure."""
    current = d
    for key in keys:
        try:
            if isinstance(current, list):
                current = current[key]
            else:
                current = current[key]
        except (KeyError, IndexError, TypeError):
            path = " -> ".join(str(k) for k in keys)
            raise ValueError(f"Missing field '{label}' at path: {path}")
    return current


def process_data_json(data):
    try:
        connectionid = _get_nested(
            data,
            'MessageDocumentHeader', 'MessageDocumentHeader_MetaInformation', 'connectionid',
            label='connectionid'
        )
    except ValueError as e:
        logger.error(f"[json_processor] Cannot extract connectionid: {e}")
        return

    try:
        user_profile = UserProfile.objects.get(connection_id=connectionid)
    except UserProfile.DoesNotExist:
        logger.error(f"[json_processor] UserProfile with connectionid {connectionid} not found.")
        return

    try:
        time_series_list = _get_nested(
            data,
            'ValidatedHistoricalData_MarketDocument', 'TimeSeriesList', 'TimeSeries',
            label='TimeSeries'
        )
        if not isinstance(time_series_list, list) or len(time_series_list) == 0:
            raise ValueError("TimeSeries is empty or not a list")

        ts0 = time_series_list[0]

        series_period_list = _get_nested(ts0, 'Series_PeriodList', 'Series_Period', label='Series_Period')
        if not isinstance(series_period_list, list) or len(series_period_list) == 0:
            raise ValueError("Series_Period is empty or not a list")

        sp0 = series_period_list[0]

        start_text        = _get_nested(sp0, 'timeInterval', 'start', label='timeInterval/start')
        resolution_text   = _get_nested(sp0, 'resolution', label='resolution')
        points_list       = _get_nested(sp0, 'PointList', 'Point', label='PointList/Point')
        metering_point    = _get_nested(ts0, 'marketEvaluationPoint.mRID', 'value', label='marketEvaluationPoint')
        data_need_id      = _get_nested(
            data, 'MessageDocumentHeader', 'MessageDocumentHeader_MetaInformation', 'dataNeedid',
            label='dataNeedid'
        )
        permission_id     = _get_nested(
            data, 'MessageDocumentHeader', 'MessageDocumentHeader_MetaInformation', 'permissionid',
            label='permissionid'
        )

        start_datetime    = parse(start_text)
        metering_interval = isodate.parse_duration(resolution_text)

        if not isinstance(points_list, list) or len(points_list) == 0:
            raise ValueError("PointList/Point is empty or not a list")

    except (ValueError, isodate.isoerror.ISO8601Error) as e:
        logger.error(f"[json_processor] Failed to parse message for connection_id={connectionid}: {e}")
        return

    with transaction.atomic():
        mp_obj, _ = MeteringPoint.objects.get_or_create(
            user_profile=user_profile,
            metering_point=metering_point,
            defaults={
                'connection_id': connectionid,
                'data_need_id': data_need_id,
                'permission_id': permission_id,
            }
        )

        ts_meta, created_ts = TimeSeriesMeta.objects.get_or_create(
            metering_point=mp_obj,
            start_datetime=start_datetime,
            defaults={'metering_interval': metering_interval}
        )

        if not created_ts and ts_meta.metering_interval != metering_interval:
            ts_meta = TimeSeriesMeta.objects.create(
                metering_point=mp_obj,
                start_datetime=start_datetime,
                metering_interval=metering_interval
            )

        for cp in points_list:
            try:
                position = int(cp['position'])
                value    = float(cp['energy_Quantity.quantity'])
                timestamp = start_datetime + relativedelta(
                    seconds=(metering_interval.total_seconds() * position)
                )

                Consumption.objects.get_or_create(
                    time_series_meta=ts_meta,
                    timestamp=timestamp,
                    defaults={'consumption_value': value}
                )
            except (KeyError, TypeError, ValueError) as e:
                logger.error(f"[json_processor] Skipping point due to invalid data: {e}")
                continue

    logger.info(f"[json_processor] Consumption data saved for user '{user_profile.user.username}'.")
