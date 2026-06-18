import logging
import os
from typing import Optional

# ------------------------- Logging -------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("mqtt-service")

# ------------------------- ENV -----------------------------
MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "aiida/v1/#")

# Filter (* = kein Filter)
def _parse_csv_set(val: Optional[str]) -> Optional[set]:
    if not val or val.strip() in ("*", ""):
        return None
    return {x.strip() for x in val.split(",") if x.strip()}


FILTER_CONN = _parse_csv_set(os.getenv("MQTT_CONNECTION_IDS", "*"))
FILTER_PERM = _parse_csv_set(os.getenv("MQTT_PERMISSION_IDS", "*"))

# DB
PG_DB = os.getenv("TIMESCALEDB_NAME", "timescale")
PG_USER = os.getenv("TIMESCALEDB_USERNAME", "postgres")
PG_PWD = os.getenv("TIMESCALEDB_PASSWORD", "eddie")
PG_HOST = os.getenv("TIMESCALEDB_HOST", "timescale")
PG_PORT = int(os.getenv("TIMESCALEDB_PORT", "5432"))

DEBUG_DROP = os.getenv("DEBUG", "False").lower() in ("1", "true", "yes")