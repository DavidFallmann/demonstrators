# -*- encoding: utf-8 -*-


from django.urls import path
from .views import index, login_view, register_user, post_registration, logout_view


urlpatterns = [
    path('login/', login_view, name="login"),
    path('register/', register_user, name="register"),
    path('post_registration/', post_registration, name="post_registration"),
    path('logout/', logout_view, name="logout"),
]
