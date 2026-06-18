import logging.config
import logging.config

from common_models.common_models_app.models import EmissionData, MeteringPoint, Consumption, UserProfile
from web_app.apps.entsoe.services.process_entsoe_data import process_entsoe_data
from web_app.core.settings import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

def assemble_emission_data(request):
    emission_data = {}
    emission_start_end = {}
    user_profile = UserProfile.objects.get(user=request.user)
    metering_points = MeteringPoint.objects.filter(user_profile=user_profile)

    for metering_point in metering_points:
        consumption_qs = __fetch_consumption(metering_point)
        if not consumption_qs.exists():
            logger.info("No consumption data found for metering_point: %s", metering_point.metering_point)
            continue

        emission_qs = __fetch_emissions(metering_point)
        earliest_timestamp_consumption = consumption_qs.first().timestamp
        latest_timestamp_consumption = consumption_qs.last().timestamp

        if emission_qs.exists():
            emission_data_per_mp, emission_start_end_per_mp = __update_emissions(
                emission_qs, latest_timestamp_consumption, metering_point, user_profile.connection_id
            )
        else:
            logger.info("Initial ENTSO-E load for %s", metering_point.metering_point)
            emission_data_per_mp, emission_start_end_per_mp = __process_entsoe_data(
                earliest_timestamp_consumption, latest_timestamp_consumption, metering_point, user_profile.connection_id
            )

        emission_data[metering_point.metering_point] = emission_data_per_mp
        emission_start_end[metering_point.metering_point] = emission_start_end_per_mp

    return {
        'emission_data': emission_data,
        'emission_start_end': emission_start_end,
    }


def __update_emissions(emission_qs, latest_timestamp_consumption, metering_point, connection_id):
    earliest_emission = emission_qs.first().timestamp
    latest_emission = emission_qs.last().timestamp

    if latest_timestamp_consumption > latest_emission:
        logger.info("Trigger ENTSO-E (backfill) for %s", metering_point.metering_point)
        emission_data_per_mp, emission_start_end_per_mp = __process_entsoe_data(
            latest_emission, latest_timestamp_consumption, metering_point, connection_id
        )
    else:
        emission_data_per_mp = list(emission_qs.values('timestamp', 'emission_value'))
        emission_start_end_per_mp = {'start': earliest_emission, 'end': latest_emission}

    return emission_data_per_mp, emission_start_end_per_mp


def __process_entsoe_data(start_datetime, end_datetime, metering_point, connection_id):
    process_entsoe_data(connection_id, start_datetime.isoformat(), end_datetime.isoformat())
    emission_qs = __fetch_emissions(metering_point)

    emission_data, emission_start_end = {}, {}
    if emission_qs.exists():
        emission_data = list(emission_qs.values('timestamp', 'emission_value'))
        emission_start_end = {'start': emission_qs.first().timestamp, 'end': emission_qs.last().timestamp}

    return emission_data, emission_start_end


def __fetch_emissions(metering_point):
    return (
        EmissionData.objects
        .filter(time_series_meta__metering_point=metering_point)
        .order_by('timestamp')
    )


def __fetch_consumption(metering_point):
    return (
        Consumption.objects
        .filter(time_series_meta__metering_point=metering_point)
        .order_by('timestamp')
    )
