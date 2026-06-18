# -*- encoding: utf-8 -*-
import uuid

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse

from common_models.common_models_app.models import UserProfile
from .forms import LoginForm, SignUpForm
from .utils import log_external


@login_required(login_url='/login/')
def index(request):
    return render(request, 'home/index.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect("index")

    form = LoginForm(request.POST or None)
    msg = None

    if request.method == "POST":
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                try:
                    log_external(participant_id=user.id, state=1, comment=f"In, {username}")
                except Exception:
                    pass
                return redirect("/")
            else:
                msg = 'Invalid credentials'
        else:
            msg = 'Error validating the form'

    return render(request, "accounts/login.html", {"form": form, "msg": msg})

def logout_view(request):
    pid = request.user.id if request.user.is_authenticated else 0
    uname = request.user.username if request.user.is_authenticated else None

    try:
        log_external(participant_id=pid, state=3, comment=f"Out, {uname}")
    except Exception:
        pass

    logout(request)
    request.session.flush()
    return redirect("login")

def generate_connection_id():
    return str(uuid.uuid4())

def register_user(request):
    msg = None
    success = False

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)

            # Login the user
            login(request, user)
            UserProfile.objects.create(user=user, connection_id=generate_connection_id())
           
            msg = 'User created successfully.'
            success = True

            # Redirect to post registration page
            return redirect(reverse('post_registration'))
        else:
            msg = 'Form is not valid'
    else:
        form = SignUpForm()

    return render(request, "accounts/register.html", {"form": form, "msg": msg, "success": success})



def post_registration(request):
    user_profile = UserProfile.objects.get(user=request.user)
    user_name = UserProfile.objects.get(user=request.user).user.username
   
    context = {
        'connection_id': user_profile.connection_id,
        'username': user_name
    }
    return render(request, 'post_registration.html', context)

