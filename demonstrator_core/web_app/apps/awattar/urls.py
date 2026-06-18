from django.urls import path

from web_app.apps.awattar.views import awattar_data

urlpatterns = [
    path('api/awattar/', awattar_data, name='awattar'),
]
