import logging.config
import xml.etree.ElementTree as ET

import isodate
from dateutil.parser import parse as parse_datetime
from dateutil.relativedelta import relativedelta
from django.db import transaction

from common_models.common_models_app.models import UserProfile, MeteringPoint, TimeSeriesMeta, Consumption
from web_app.core.settings import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

def _find_text(element, path, ns=None, label="field"):
    found = element.find(path, ns) if ns else element.find(path)
    if found is None or found.text is None:
        raise ValueError(f"Missing or empty XML element: '{label}' (path={path})")
    return found.text.strip()


def process_data_xml(data):
    ns_outer = {'ns': 'http://www.eddie.energy/agnostic'}

    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        logger.error(f"[xml_processor] Failed to parse outer XML: {e}")
        return

    try:
        connection_id = _find_text(root, 'ns:connectionId', ns_outer, 'connectionId')
        permission_id = _find_text(root, 'ns:permissionId', ns_outer, 'permissionId')
        data_need_id  = _find_text(root, 'ns:dataNeedId',   ns_outer, 'dataNeedId')
        raw_payload   = _find_text(root, 'ns:rawPayload',   ns_outer, 'rawPayload')
    except ValueError as e:
        logger.error(f"[xml_processor] Outer envelope incomplete: {e}")
        return

    try:
        user_profile = UserProfile.objects.get(connection_id=connection_id)
    except UserProfile.DoesNotExist:
        logger.error(f"[xml_processor] UserProfile with connectionid {connection_id} not found.")
        return

    try:
        payload_root = ET.fromstring(raw_payload)
    except ET.ParseError as e:
        logger.error(f"[xml_processor] Failed to parse rawPayload XML: {e}")
        return

    try:
        time_series = payload_root.find('.//TimeSeries')
        if time_series is None:
            raise ValueError("TimeSeries element not found")

        period = time_series.find('.//Series_Period')
        if period is None:
            raise ValueError("Series_Period element not found")

        time_interval = period.find('.//timeInterval')
        if time_interval is None:
            raise ValueError("timeInterval element not found")

        start_text = _find_text(time_interval, 'start', label='timeInterval/start')
        start_datetime = parse_datetime(start_text)

        resolution_text = _find_text(period, 'resolution', label='resolution')
        metering_interval = isodate.parse_duration(resolution_text)

        metering_point = _find_text(time_series, 'marketEvaluationPoint.mRID/value', label='marketEvaluationPoint')

        point_list = period.find('PointList')
        if point_list is None:
            raise ValueError("PointList element not found")
        points = point_list.findall('Point')
        if not points:
            raise ValueError("PointList contains no Point elements")

    except (ValueError, isodate.isoerror.ISO8601Error) as e:
        logger.error(f"[xml_processor] Failed to parse payload for connection_id={connection_id}: {e}")
        return

    with transaction.atomic():
        mp_obj, _ = MeteringPoint.objects.get_or_create(
            user_profile=user_profile,
            metering_point=metering_point,
            defaults={
                'connection_id': connection_id,
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
                metering_interval=metering_interval,
            )

        for point in points:
            try:
                position_el = point.find('position')
                value_el    = point.find('energy_Quantity.quantity')

                if position_el is None or position_el.text is None:
                    logger.warning("[xml_processor] Skipping point: missing 'position'")
                    continue
                if value_el is None or value_el.text is None:
                    logger.warning("[xml_processor] Skipping point: missing 'energy_Quantity.quantity'")
                    continue

                position  = int(position_el.text)
                value     = float(value_el.text)
                timestamp = start_datetime + relativedelta(
                    seconds=(metering_interval.total_seconds() * position)
                )

                Consumption.objects.get_or_create(
                    time_series_meta=ts_meta,
                    timestamp=timestamp,
                    defaults={'consumption_value': value}
                )
            except (ValueError, TypeError) as e:
                logger.error(f"[xml_processor] Skipping point due to invalid data: {e}")
                continue

    logger.info(f"[xml_processor] Consumption data saved for user '{user_profile.user.username}'.")
