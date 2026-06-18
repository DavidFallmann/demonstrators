# views.py
import json
import time
from datetime import datetime, timedelta, timezone

from django.http import StreamingHttpResponse
from django.db import connection


def sse_mqtt_stream(request):
    """
    Sehr einfache SSE-Quelle: schickt alle X Sekunden neue Messungen.
    """

    # optional später: user_id = request.GET.get("user_id")

    def event_stream():
        # wir merken uns den letzten Timestamp
        last_ts = datetime.now(timezone.utc) - timedelta(seconds=2)

        while True:
            # neue Messungen seit last_ts holen
            with connection.cursor() as cur:
                cur.execute(
                    """
                    SELECT ts, tag, value_numeric
                    FROM mqtt_measurements
                    WHERE ts > %s
                    ORDER BY ts ASC
                    """,
                    [last_ts],
                )
                rows = cur.fetchall()

            if rows:
                # letzten TS auf den neuesten setzen
                last_ts = rows[-1][0]

                payload = [
                    {
                        "ts": r[0].isoformat(),
                        "tag": r[1],
                        "value": r[2],
                    }
                    for r in rows
                ]

                # SSE-Format: data: ... \n\n
                yield f"data: {json.dumps(payload)}\n\n"

            # ein bisschen schlafen, damit wir nicht die DB fluten
            time.sleep(2)

    resp = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    resp["Cache-Control"] = "no-cache"
    return resp
