from django.http import JsonResponse

from web_app.apps.consumption.services.assemble_consumption_data import assemble_consumption_data
from web_app.apps.util import log_time


def consumption_data(request):
    with log_time("consumption_data"):
        data = assemble_consumption_data(request)
    return JsonResponse(data)
