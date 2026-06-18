import datetime
import json
from typing import Any, Dict, Tuple, Optional

import xmltodict


def parse_payload(payload: bytes) -> Dict[str, Any]:
    """
    Versuche zuerst JSON, dann XML->JSON; bei Fehlschlag als {'_raw': str}.
    """
    text = payload.decode("utf-8", errors="replace").strip()
    # JSON
    try:
        return json.loads(text)
    except Exception:
        pass
    # XML -> JSON
    try:
        data = xmltodict.parse(text)
        return json.loads(json.dumps(data))
    except Exception:
        return {"_raw": text}


def _dig(obj: Any, *path) -> Any:
    cur = obj
    for p in path:
        if isinstance(cur, dict) and isinstance(p, str):
            if p in cur:
                cur = cur[p]
            else:
                return None
        elif isinstance(cur, list) and isinstance(p, int):
            if 0 <= p < len(cur):
                cur = cur[p]
            else:
                return None
        else:
            return None
    return cur


def _get_flat(obj: Dict[str, Any], dotted_key: str) -> Any:
    """Erwartet 'flattened' JSON mit Keys wie 'a.b.c' (genau so als Key im dict)."""
    if not isinstance(obj, dict):
        return None
    return obj.get(dotted_key)


def extract_ids(doc: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Liefert (user_id, connection_id, permission_id, data_source_id), tolerant für:
    - 'flache' Keys wie messageDocumentHeader.metaInformation.connectionId
    - 'normale' Keys wie doc['userId']
    """
    user_id = (
            _get_flat(doc, "messageDocumentHeader.metaInformation.finalCustomerId")
            or doc.get("userId")
    )
    connection_id = (
            _get_flat(doc, "messageDocumentHeader.metaInformation.connectionId")
            or doc.get("connectionId")
    )
    permission_id = (
            _get_flat(doc, "messageDocumentHeader.metaInformation.permissionId")
            or doc.get("permissionId")
    )
    data_source_id = (
            _get_flat(doc, "messageDocumentHeader.metaInformation.dataSourceId")
            or doc.get("dataSourceId")
    )
    return (
        str(user_id) if user_id is not None else None,
        str(connection_id) if connection_id is not None else None,
        str(permission_id) if permission_id is not None else None,
        str(data_source_id) if data_source_id is not None else None,
    )


def extract_ts(doc: Dict[str, Any]) -> str:
    """
    Versucht, einen ISO-Timestamp zu finden; fällt auf 'jetzt' (UTC) zurück.
    Prüft sowohl 'flache' als auch verschachtelte Pfade.
    """
    candidates = [
        ("timestamp",),  # einfache Form
        ("dateTime",),  # manche Payloads
        ("dateAndOrTime.dateTime",),  # flattened Form
        ("MarketDocument", "createdDateTime"),
        ("MarketDocument", "TimeSeries", 0, "dateAndOrTime.dateTime"),
    ]
    for path in candidates:
        if len(path) == 1 and "." in path[0]:
            val = _get_flat(doc, path[0])
        else:
            val = _dig(doc, *path)
        if val:
            return str(val)

    return datetime.now(datetime.timezone.utc).isoformat()