import logging.config
from datetime import timezone, datetime

import isodate

from common_models.common_models_app.models import UserProfile, MeteringPoint, TimeSeriesMeta, Consumption, EmissionData
from web_app.apps.entsoe.clients.entsoe_client import fetch_data_from_entsoe
from web_app.core.settings import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


# ENTSO-E zone = first 2 chars of the metering point ID (e.g. 'AT', 'DE').
# Skip virtual/simulation metering points like 'mid' whose zone would
# not be a valid ENTSO-E country code.
VALID_ZONES = {
    'AL','AT','BA','BE','BG','BY','CH','CY','CZ','DE','DK','EE','ES',
    'FI','FR','GB','GE','GR','HR','HU','IE','IT','LT','LU','LV','MD',
    'ME','MK','MT','NL','NO','PL','PT','RO','RS','RU','SE','SI','SK',
    'TR','UA','XK',
}

def process_entsoe_data(connection_id, start_dt, end_dt):
    logger.debug(f"Starting ENTSOE Process (connection_id={connection_id}, start={start_dt}, end={end_dt})")

    user_profile = UserProfile.objects.get(connection_id=connection_id)
    metering_points = MeteringPoint.objects.filter(user_profile=user_profile)
    for mp in metering_points:
        time_series_metas = TimeSeriesMeta.objects.filter(metering_point=mp)
        for ts_meta in time_series_metas:

            consumption_qs = __fetch_consumption_data(end_dt, start_dt, ts_meta)
            emissions = __fetch_emissions(ts_meta, start_dt, end_dt)

            if not consumption_qs.exists():
                continue
            if emissions.exists():
                logger.debug(
                    f"Emission data already exists for user_profile {user_profile.user.username}, MP={mp.metering_point}, skipping.")
                continue

            response = __fetch_data_from_entsoe(consumption_qs, mp, ts_meta)
            if response:
                logger.debug(f"Response for user_profile={user_profile.user.username}, MP={mp.metering_point}")
                __persist_emission_data(ts_meta, response)
            else:
                logger.debug(f"No data returned for user_profile: {user_profile.user.username}, MP={mp.metering_point}")


def __fetch_consumption_data(end_dt, start_dt, ts_meta):
    consumption_qs = Consumption.objects.filter(
        time_series_meta=ts_meta,
        timestamp__gte=start_dt,
        timestamp__lte=end_dt
    ).order_by('timestamp')
    return consumption_qs


def __fetch_emissions(ts_meta, start_dt, end_dt):
    return EmissionData.objects.filter(
        time_series_meta=ts_meta,
        timestamp__gte=start_dt,
        timestamp__lte=end_dt
    )


def __fetch_data_from_entsoe(consumption_qs, mp, ts_meta):
    consumption_data = list(consumption_qs.values_list('consumption_value', flat=True))
    zone = mp.metering_point[:2].upper()
    if zone not in VALID_ZONES:
        logger.debug(f"Skipping MP={mp.metering_point!r} — zone {zone!r} is not a valid ENTSO-E zone.")
        return None

    unit = ts_meta.unit
    metering_interval = isodate.duration_isoformat(ts_meta.metering_interval)
    start_datetime = consumption_qs.first().timestamp
    end_datetime = consumption_qs.last().timestamp

    return fetch_data_from_entsoe(zone, start_datetime, end_datetime, unit, metering_interval, consumption_data)


def __persist_emission_data(ts_meta, response):
    response_interval_timedelta = isodate.parse_duration(response["resolution"])
    emission_for_all_consumption_list = response["consumption"]
    response_start_datetime = datetime.strptime(response["start"], "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
    response_unit = response["unit"]

    for index, value in enumerate(emission_for_all_consumption_list):
        EmissionData.objects.get_or_create(
            time_series_meta=ts_meta,
            timestamp=response_start_datetime + (index * response_interval_timedelta),
            defaults={
                'emission_value': value,
                'unit': response_unit
            }
        )
