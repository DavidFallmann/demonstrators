# common_models_app/services/aiida_ingest.py
import json
from datetime import datetime, timezone
from django.utils.dateparse import parse_datetime
from common_models.common_models_app.models import UserAiidaRealTimeData

def _parse_iso(ts: str):
    dt = parse_datetime(ts) or datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

def _extract_first_quantity(payload: dict):
    md = payload.get("MarketDocument", {}) if isinstance(payload, dict) else {}
    ts_list = md.get("TimeSeries", []) or []
    ts_obj = ts_list[0] if ts_list else {}
    quantities = ts_obj.get("Quantity", []) or [{}]
    q = quantities[0]
    ts_str = ts_obj.get("dateAndOrTime.dateTime") or md.get("createdDateTime") or datetime.now(timezone.utc).isoformat()
    meta = (payload.get("messageDocumentHeader", {}) or {}).get("metaInformation", {}) if isinstance(payload, dict) else {}

    return {
        "timestamp": _parse_iso(ts_str),
        "quantity_type": str(q.get("type", "")),
        "quality": str(q.get("quality", "")),
        "quantity": int(q.get("quantity", 0) or 0),
        "market_document_mrid": md.get("mRID", ""),
        "data_need_id": meta.get("dataNeedId", ""),
        "connection_id": meta.get("connectionId", ""),
        "data_source_id": meta.get("dataSourceId", ""),
        "final_customer_id": meta.get("finalCustomerId", ""),
        "document_type": meta.get("documentType", ""),
    }

def store_rows(permission_id: str, rows: list, user=None) -> int:
    """rows: Liste von {ts, topic, payload_json} – speichert in bestehende Tabelle."""
    to_create = []
    for row in rows:
        payload = row.get("payload_json")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {"raw": payload}

        if isinstance(payload, dict):
            f = _extract_first_quantity(payload)
            ts = f["timestamp"]
        else:
            f = {"quantity_type":"", "quality":"", "quantity":0,
                 "market_document_mrid":"", "data_need_id":"",
                 "connection_id":"", "data_source_id":"",
                 "final_customer_id":"", "document_type":""}
            ts = _parse_iso(row.get("ts"))

        to_create.append(UserAiidaRealTimeData(
            user=user if (getattr(user, "is_authenticated", False)) else None,
            permission_id=permission_id,
            timestamp=ts,
            quantity_type=f["quantity_type"],
            quality=f["quality"],
            quantity=f["quantity"],
            market_document_mrid=f["market_document_mrid"],
            data_need_id=f["data_need_id"],
            connection_id=f["connection_id"],
            data_source_id=f["data_source_id"],
            final_customer_id=f["final_customer_id"],
            document_type=f["document_type"],
            raw=payload if isinstance(payload, dict) else {"raw": payload},
        ))
    if to_create:
        UserAiidaRealTimeData.objects.bulk_create(to_create)
    return len(to_create)
