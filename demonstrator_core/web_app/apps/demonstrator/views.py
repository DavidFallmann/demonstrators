import csv
import json
import logging.config
import uuid
from datetime import datetime

import requests
from django import template
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import render
from django.template import loader
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from isodate import parse_datetime

from web_app.apps.authentication.utils import log_external
from web_app.apps.demonstrator.services.compare_prices import compare_prices
from web_app.core.settings import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

from common_models.common_models_app.models import (
    UserProfile, MeteringPoint, Consumption,
    UserPermission, MqttMeasurement
)


@login_required(login_url="/login/")
def index(request):
    user_profile = UserProfile.objects.get(user=request.user)
    metering_points = MeteringPoint.objects.filter(user_profile=user_profile)

    context = {
        'metering_points_json': json.dumps(list(metering_points.values()), cls=DjangoJSONEncoder),
        **compare_prices(request),
    }
    try:
        log_external(participant_id=request.user.id, state=2, comment="index_opened")
    except Exception:
        pass

    html_template = loader.get_template('home/index.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:
        load_template = request.path.split('/')[-1]
        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template

        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:
        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except Exception:
        html_template = loader.get_template('home/page-500.html')
        return HttpResponse(html_template.render(context, request))


@login_required
def download_consumption_data(request):
    user_profile = UserProfile.objects.get(user=request.user)
    metering_points = MeteringPoint.objects.filter(user_profile=user_profile)
    user_name = user_profile.user.username

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="consumption_data.csv"'

    writer = csv.writer(response)

    writer.writerow([f'USER: {user_name}'])
    writer.writerow([f'CREATION DATE: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
    writer.writerow([])

    for mp in metering_points:
        consumptions = Consumption.objects.filter(
            time_series_meta__metering_point=mp
        ).order_by('timestamp')

        if consumptions.exists():
            earliest_timestamp = consumptions.first().timestamp
            latest_timestamp = consumptions.last().timestamp
            time_series_meta = consumptions.first().time_series_meta
            interval = time_series_meta.metering_interval

            writer.writerow([f'METERING POINT: {mp.metering_point}'])
            writer.writerow([f'START: {earliest_timestamp}'])
            writer.writerow([f'END: {latest_timestamp}'])
            writer.writerow([f'INTERVAL: {interval}'])
            writer.writerow([])
            writer.writerow(['Timestamp', 'Consumption Value'])

            for consumption in consumptions:
                writer.writerow([consumption.timestamp, consumption.consumption_value])

            writer.writerow([])

    return response


@login_required
def aiida_view(request):
    perms = (UserPermission.objects
             .filter(user=request.user, verified=True)
             .values_list('permission_id', flat=True)
             .distinct())
    my_permissions = [{'permission_id': str(p), 'verified': True} for p in perms]
    show_setup = (len(my_permissions) == 0)

    return render(request, "home/aiida.html", {
        "segment": "aiida",
        "my_permissions": my_permissions,
        "show_setup": show_setup,
    })


@login_required
@require_http_methods(["POST", "GET"])
def verify_permission(request):
    perm_raw = request.POST.get('permission_id') or request.GET.get('permission_id')
    if not perm_raw:
        return JsonResponse({"status": "error", "error": "missing permission_id"}, status=400)

    try:
        perm_uuid = uuid.UUID(str(perm_raw))
    except ValueError:
        return JsonResponse({"status": "error", "error": "invalid permission_id (must be UUID)"}, status=400)

    obj, created = UserPermission.objects.get_or_create(
        user=request.user,
        permission_id=perm_uuid,
        defaults={"verified": True},
    )

    if not created and not obj.verified:
        obj.verified = True
        obj.save(update_fields=["verified"])

    return JsonResponse({"status": "ok", "created": created, "verified": obj.verified})


@login_required
def aiida_stream(request):
    perm_raw = request.GET.get('permission_id')
    since = request.GET.get('since')

    if not perm_raw:
        return JsonResponse({"status": "error", "error": "missing permission_id"}, status=400)

    # Permission-ID validieren
    try:
        perm_uuid = uuid.UUID(str(perm_raw))
    except ValueError:
        return JsonResponse({"status": "error", "error": "invalid permission_id (must be UUID)"}, status=400)

    # Zugriff: nur wenn der User diese permission_id besitzt & verifiziert ist
    if not UserPermission.objects.filter(user=request.user, permission_id=perm_uuid, verified=True).exists():
        return JsonResponse({"status": "forbidden"}, status=403)

    # Aus mqtt_measurements lesen
    qs = MqttMeasurement.objects.filter(permission_id=str(perm_uuid))

    if since:
        # Robustly parse ISO datetime — handle Z, +00:00, and space-separated formats
        dt = None
        try:
            dt = parse_datetime(since)
            if dt is None:
                # Fallback: replace Z with +00:00 and retry
                from datetime import datetime as _dt, timezone as _tz
                dt = _dt.fromisoformat(since.replace('Z', '+00:00'))
        except Exception:
            dt = None

        if dt:
            qs = qs.filter(ts__gt=dt)
        rows = list(qs.order_by('ts')[:500])
    else:
        # Erster Abruf: neueste 500 Einträge zurückgeben, chronologisch sortiert
        rows = list(qs.order_by('-ts')[:500])
        rows.reverse()

    data = []
    for r in rows:
        value = float(r.value_numeric) if r.value_numeric is not None else None
        data.append({
            "ts": r.ts.isoformat(),
            "tag": r.tag or "value",
            "unit": r.unit or "",
            "value": value,
            "payload_json": r.raw_json,
        })

    last_ts = data[-1]["ts"] if data else (since or None)
    return JsonResponse({"status": "ok", "data": data, "last_ts": last_ts})


@login_required
@require_http_methods(["POST", "DELETE", "GET"])
def delete_permission(request):
    perm_raw = request.POST.get('permission_id') or request.GET.get('permission_id')
    if not perm_raw:
        return JsonResponse({"status": "error", "error": "missing permission_id"}, status=400)
    try:
        perm_uuid = uuid.UUID(str(perm_raw))
    except ValueError:
        return JsonResponse({"status": "error", "error": "invalid permission_id"}, status=400)

    deleted, _ = UserPermission.objects.filter(
        user=request.user, permission_id=perm_uuid
    ).delete()
    return JsonResponse({"status": "ok", "deleted": deleted > 0})

@csrf_exempt
def proxy_log(request):
    participant_id = request.GET.get("participant_id")
    state = request.GET.get("state")
    comment = request.GET.get("comment", "0")

    target_url = "https://flo.cosylab.at/eddie/inspectors_v1/logNik.php"

    try:
        response = requests.get(target_url, params={
            "participant_id": participant_id,
            "state": state,
            "comment": comment
        })
        return JsonResponse({'status': response.status_code})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
