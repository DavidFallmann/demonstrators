from django.http import JsonResponse

from web_app.apps.entsoe.services.assemble_emission_data import assemble_emission_data
from web_app.apps.util import log_time


def emission_data(request):
    with log_time("emission_data"):
        data = assemble_emission_data(request)
    return JsonResponse(data)