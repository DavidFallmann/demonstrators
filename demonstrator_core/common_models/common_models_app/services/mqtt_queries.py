# mqtt_queries.py
from __future__ import annotations
from django.db import connection

def energy_15m_all(hours: int = 24, tag: str | None = None):
    params = {"hours": hours}
    tag_filter = ""
    if tag:
        tag_filter = "AND tag = %(tag)s"
        params["tag"] = tag

    sql = f"""
        SELECT time_bucket('15 minutes', ts) AS bucket,
               SUM(value_numeric)           AS energy_kwh
        FROM mqtt_measurements
        WHERE unit = 'kWh'
          {tag_filter}
          AND ts >= NOW() - (%(hours)s || ' hours')::interval
        GROUP BY bucket
        ORDER BY bucket;
    """
    with connection.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return [{"bucket": r[0], "energy_kwh": float(r[1] or 0)} for r in rows]
