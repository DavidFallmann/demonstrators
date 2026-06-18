import logging.config

from django.http import JsonResponse

from web_app.apps.awattar.services.fetch_awattar_data import fetch_awattar_data
from web_app.apps.util import log_time
from web_app.core.settings import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


def awattar_data(request):
    with log_time("awattar_data"):
        data = fetch_awattar_data()

    return JsonResponse(data)
