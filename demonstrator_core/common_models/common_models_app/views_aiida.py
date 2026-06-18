# common_models_app/views_aiida.py
from datetime import datetime, timezone
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from common_models.common_models_app.models import UserAiidaRealTimeData
from common_models.common_models_app.services.aiida_queries import store_rows

@login_required(login_url='blogin')
def my_permission(request):
    last = (UserAiidaRealTimeData.objects
            .filter(user=request.user)
            .order_by("-timestamp")
            .first())
    if not last:
        return JsonResponse({"has_permission": False})
    return JsonResponse({"has_permission": True, "permission_id": str(last.permission_id)})

@login_required(login_url='blogin')
def verify_permission(request):
    permission_id = request.GET.get("permission_id")
    since = request.GET.get("since")
    if not permission_id:
        return HttpResponseBadRequest("permission_id required")

    now_iso = datetime.now(timezone.utc).isoformat()
    demo_rows = [{
        "ts": now_iso,
        "topic": "near-real-time-market-document",
        "payload_json": {
            "MarketDocument": {
                "mRID": "demo",
                "TimeSeries": [{
                    "Quantity": [{"type":"0","quality":"AS_PROVIDED","quantity":123}],
                    "dateAndOrTime.dateTime": now_iso
                }]
            },
            "messageDocumentHeader": {"metaInformation": {
                "permissionId": permission_id,
                "documentType": "near-real-time-market-document",
                "dataNeedId": "a42d21be-0b81-4189-9115-46fc5a5c2896"
            }}
        }
    }]
    response_payload = {"status": "ok", "data": demo_rows, "last_ts": now_iso}

    created = store_rows(permission_id, response_payload["data"], request.user)
    response_payload["stored"] = created

    return JsonResponse(response_payload)
