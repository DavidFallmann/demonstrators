from django.urls import path

from web_app.apps.entsoe.views import emission_data

urlpatterns = [
    path('api/emissions/', emission_data, name='emissions'),
]
