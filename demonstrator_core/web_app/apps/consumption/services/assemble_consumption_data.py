import logging.config

from common_models.common_models_app.models import MeteringPoint, UserProfile, Consumption
from web_app.core.settings import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

def assemble_consumption_data(request):
    user_profile = UserProfile.objects.get(user=request.user)
    metering_points = MeteringPoint.objects.filter(user_profile=user_profile)

    consumption_data = {}
    consumption_start_end = {}
    for metering_point in metering_points:
        consumption_qs = (
            Consumption.objects
            .filter(time_series_meta__metering_point=metering_point)
            .order_by('timestamp')
        )
        if not consumption_qs.exists():
            logger.info("No consumption data found for metering_point: %s", metering_point.metering_point)
            continue


        consumption_data[metering_point.metering_point] = list(
            consumption_qs.values('timestamp', 'consumption_value')
        )
        consumption_start_end[metering_point.metering_point] = {
            'start': consumption_qs.first().timestamp,
            'end': consumption_qs.last().timestamp,
        }

    return {
        'consumption_data': consumption_data,
        'consumption_start_end': consumption_start_end,
    }