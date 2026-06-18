import os

from django.conf import settings
from django.contrib import admin
from django.http import HttpResponseNotFound, FileResponse
from django.urls import path, include, re_path


def service_worker(request):
    candidates = [
        os.path.join(settings.BASE_DIR, "web_app", "apps", "static", "pwabuilder-sw.js"),
        os.path.join(settings.BASE_DIR, "apps", "static", "pwabuilder-sw.js"),
        os.path.join(settings.BASE_DIR, "static", "pwabuilder-sw.js"),
    ]
    for sw_path in candidates:
        if os.path.exists(sw_path):
            return FileResponse(open(sw_path, "rb"), content_type="application/javascript")

    return HttpResponseNotFound("pwabuilder-sw.js not found. Tried: " + " | ".join(candidates))


urlpatterns = [
    re_path(r"^pwabuilder-sw\.js$", service_worker),

    path('admin/', admin.site.urls),
    path("", include("web_app.apps.consumption.urls")),
    path("", include("web_app.apps.awattar.urls")),
    path("", include("web_app.apps.predictions.urls")),
    path("", include("web_app.apps.entsoe.urls")),
    path("", include("web_app.apps.authentication.urls")),
    path("", include("web_app.apps.demonstrator.urls")),
]
