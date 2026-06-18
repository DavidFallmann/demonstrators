# common_models/common_models_app/views_mqtt.py

from uuid import UUID
import json
import logging

from django.http import JsonResponse
from django.db import connection, transaction
from django.utils.dateparse import parse_datetime
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser

from .models import UserAiidaRealTimeData, UserPermission

logger = logging.getLogger(__name__)


def _to_uuid(v):
    try:
        return UUID(str(v))
    except Exception:
        return None


def _ensure_dict(val):
    """
    Stellt sicher, dass payload als dict vorliegt.
    - Wenn string: JSON-parsen, sonst in {"raw": "..."} packen.
    - Wenn dict: zurückgeben.
    """
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return {"raw": val}
    return {"raw": val}


@login_required
def verify_permission_and_get_data(request):
    """
    Holt neue Zeilen aus mqtt_messages (optional seit 'since'),
    gibt sie ans Frontend zurück und speichert sie idempotent in UserAiidaRealTimeData.
    Setzt/legt außerdem UserPermission(user, permission_id) an und markiert verified=True, wenn Daten kamen.
    """
    permission_id = request.GET.get("permission_id")
    if not permission_id:
        return JsonResponse({"status": "error", "message": "No permission_id provided."}, status=400)

    # Falls Model-Spalte UUID ist, früh prüfen:
    pid_uuid = _to_uuid(permission_id)
    if pid_uuid is None:
        return JsonResponse({"status": "error", "message": "permission_id is not a valid UUID."}, status=400)

    since = request.GET.get("since")  # optional

    # Permission-Objekt sicherstellen (noch nicht verified)
    UserPermission.objects.get_or_create(user=request.user, permission_id=pid_uuid)

    # --- Daten aus der mqtt_messages-DB holen ---
    params = [permission_id]
    sql = """
        SELECT ts, topic, payload_json
        FROM mqtt_messages
        WHERE permission_id = %s
    """
    if since:
        sql += " AND ts > %s"
        params.append(since)
    sql += " ORDER BY ts ASC LIMIT 500"

    with connection.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    data = []
    last_ts = since  # fallback
    created_count = 0

    # eingeloggter User (Absicherung)
    current_user = None if isinstance(getattr(request, "user", None), AnonymousUser) else getattr(request, "user", None)

    @transaction.atomic
    def _persist_rows():
        nonlocal created_count, last_ts

        for ts_db, topic, payload_raw in rows:
            payload = _ensure_dict(payload_raw)

            # fürs Response
            ts_iso = ts_db.isoformat() if hasattr(ts_db, "isoformat") else str(ts_db)
            data.append({"ts": ts_iso, "topic": topic, "payload_json": payload})
            last_ts = ts_iso

            # Felde aus payload extrahieren
            try:
                mdh = payload.get("messageDocumentHeader", {})
                meta = mdh.get("metaInformation", {})
                market_doc = payload.get("MarketDocument", {})

                # Quantity/Quality
                qtype = ""
                quality = ""
                quantity = 0
                try:
                    ts_list = market_doc.get("TimeSeries", [])
                    if ts_list:
                        q_list = ts_list[0].get("Quantity", [])
                        if q_list:
                            q0 = q_list[0]
                            qtype = str(q0.get("type", ""))[:32]
                            quality = str(q0.get("quality", ""))[:64]
                            q_val = q0.get("quantity", 0)
                            try:
                                quantity = int(q_val)
                            except Exception:
                                try:
                                    quantity = int(float(q_val))
                                except Exception:
                                    quantity = 0
                except Exception:
                    # Falls das Format anders ist, ales raw speichern.
                    pass

                market_document_mrid = str(market_doc.get("mRID", ""))[:64]
                data_need_id   = str(meta.get("dataNeedId", ""))[:64]
                connection_id  = str(meta.get("connectionId", ""))[:64]
                data_source_id = str(meta.get("dataSourceId", ""))[:64]
                final_customer_id = str(meta.get("finalCustomerId", ""))[:64]

                document_type  = str(meta.get("documentType") or market_doc.get("documentType") or "")[:128]

                ts_dt = ts_db
                if not hasattr(ts_dt, "tzinfo"):  # evtl. str
                    ts_dt = parse_datetime(ts_iso) or ts_db

                obj, created = UserAiidaRealTimeData.objects.get_or_create(
                    permission_id=pid_uuid,
                    timestamp=ts_dt,
                    defaults={
                        "user": current_user,
                        "quantity_type": qtype,
                        "quality": quality,
                        "quantity": quantity,
                        "market_document_mrid": market_document_mrid,
                        "data_need_id": data_need_id,
                        "connection_id": connection_id,
                        "data_source_id": data_source_id,
                        "final_customer_id": final_customer_id,
                        "document_type": document_type,
                        "raw": payload,
                    },
                )
                if created:
                    created_count += 1

            except Exception as e:
                logger.warning("Persist skip (permission_id=%s ts=%s): %s", permission_id, ts_iso, e)


        if created_count > 0:
            UserPermission.objects.filter(user=current_user, permission_id=pid_uuid).update(verified=True)

    _persist_rows()

    return JsonResponse({
        "status": "ok",
        "message": f"Data for Permission ID {permission_id}",
        "data": data,
        "last_ts": last_ts,
        "persisted": created_count
    })
