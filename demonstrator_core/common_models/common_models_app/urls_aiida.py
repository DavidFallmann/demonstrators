# common_models_app/urls_aiida.py
from django.urls import path
from .views_aiida import verify_permission, my_permission

urlpatterns = [
    path("verify_permission/", verify_permission, name="verify_permission"),
    path("my_permission/", my_permission, name="my_permission"),
]
