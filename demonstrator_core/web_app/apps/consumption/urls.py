from django.urls import path

from web_app.apps.consumption.views import consumption_data

urlpatterns = [
    path('api/consumption/', consumption_data, name='consumption'),
]
