from django.http import JsonResponse

from web_app.apps.predictions.services.assemble_prediction_data import assemble_prediction_data
from web_app.apps.util import log_time


def prediction_data(request):
    with log_time("prediction_data"):
        data = assemble_prediction_data(request)
    return JsonResponse(data)
