from django.urls import path

from web_app.apps.predictions.views import prediction_data

urlpatterns = [
    path('api/predictions/', prediction_data, name='predictions'),
]
