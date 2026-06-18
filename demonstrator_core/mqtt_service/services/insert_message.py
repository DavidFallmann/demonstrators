import json
from typing import Optional, Dict, Any, Tuple, List

from psycopg2.extras import Json

from mqtt_service.config.config import log
from mqtt_service.config.database import db_conn
from mqtt_service.services.parse_payload import extract_ts, extract_ids, _get_flat


def insert_message(
        topic: str,
        connection_id: Optional[str],
        permission_id: Optional[str],
        payload_json: Optional[Dict[str, Any]],
        raw: str,
):
    with db_conn() as con:
        with con.cursor() as cur:
            cur.execute(
                """
                INSERT INTO mqtt_messages (topic, connection_id, permission_id, payload_json, payload_raw)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    topic,
                    connection_id,
                    permission_id,
                    Json(payload_json) if payload_json else None,
                    raw,
                ),
            )


def _to_float(x) -> Optional[float]:
    if x is None:
        return None
    try:
        return float(x)
    except Exception:
        return None


def insert_measurements(
        topic: str,
        doc: Dict[str, Any],
        override_ids: Optional[Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]] = None,
):
    """
    Sucht eine Values-Liste und schreibt je Wert eine Zeile.
    Fällt auf 'einzelnen' Wert zurück, falls keine Liste vorhanden ist.

    override_ids = (user_id, connection_id, permission_id, data_source_id)
    """
    ts_iso = extract_ts(doc)

    if override_ids is not None:
        user_id, connection_id, permission_id, data_source_id = override_ids
    else:
        user_id, connection_id, permission_id, data_source_id = extract_ids(doc)

    asset = (
            _get_flat(doc, "messageDocumentHeader.metaInformation.asset")
            or doc.get("asset")
    )

    values = doc.get("values")
    rows: List[Dict[str, Any]] = []

    if isinstance(values, list) and values:
        for item in values:
            tag = item.get("dataTag") or item.get("rawTag") or "value"
            unit = item.get("unit") or item.get("rawUnitOfMeasurement")
            val = _to_float(
                item.get("value") or item.get("quantity") or item.get("rawValue")
            )
            if val is None:
                continue
            rows.append(
                {
                    "ts": ts_iso,
                    "topic": topic,
                    "user_id": user_id,
                    "connection_id": connection_id,
                    "permission_id": permission_id,
                    "data_source_id": data_source_id,
                    "asset": asset,
                    "tag": tag,
                    "value_numeric": val,
                    "unit": unit,
                    "raw_json": json.dumps(item),
                }
            )
    else:
        # Single-Value-Fallback
        tag = doc.get("dataTag") or doc.get("rawTag") or "value"
        unit = doc.get("unit") or doc.get("rawUnitOfMeasurement")
        val = _to_float(
            doc.get("value") or doc.get("quantity") or doc.get("rawValue")
        )
        if val is not None:
            rows.append(
                {
                    "ts": ts_iso,
                    "topic": topic,
                    "user_id": user_id,
                    "connection_id": connection_id,
                    "permission_id": permission_id,
                    "data_source_id": data_source_id,
                    "asset": asset,
                    "tag": tag,
                    "value_numeric": val,
                    "unit": unit,
                    "raw_json": json.dumps(doc),
                }
            )

    if not rows:
        log.debug("No measurement rows extracted for topic=%s", topic)
        return

    with db_conn() as con:
        with con.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO mqtt_measurements
                (ts, topic, user_id, connection_id, permission_id, data_source_id, asset, tag, value_numeric, unit, raw_json)
                VALUES (
                           COALESCE(%(ts)s::timestamptz, NOW()),
                           %(topic)s,
                           %(user_id)s,
                           %(connection_id)s,
                           %(permission_id)s,
                           %(data_source_id)s,
                           %(asset)s,
                           %(tag)s,
                           %(value_numeric)s,
                           %(unit)s,
                           %(raw_json)s::jsonb
                       )
                """,
                rows,
            )
    log.info("Inserted %d measurement row(s) for topic=%s", len(rows), topic)