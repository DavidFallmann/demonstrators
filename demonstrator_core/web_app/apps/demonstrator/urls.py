# web_app/apps/demonstrator/urls.py

from django.urls import path, include, re_path

from web_app.apps.demonstrator.views import (
    download_consumption_data,
    aiida_view, verify_permission, aiida_stream, index, pages, delete_permission
)

urlpatterns = [
    # The home page
    path('', index, name='home'),

    path('api/verify_permission/', verify_permission, name='dashboard_verify_permission'),
    path('api/aiida_stream/', aiida_stream, name='aiida_stream'),
    path('api/delete_permission/', delete_permission, name='delete_permission'),
    path('aiida/', aiida_view, name='aiida'),
    path('api/', include(('common_models.common_models_app.urls_aiida', 'common_aiida'), namespace='common_aiida')),

    path('dev/download_consumption_data/', download_consumption_data, name='download_consumption_data'),

    # Matches any html file
    re_path(r'^.*\.*', pages, name='pages'),
]
