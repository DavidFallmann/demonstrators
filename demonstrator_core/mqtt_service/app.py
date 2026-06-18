import uuid
from typing import Optional

from paho.mqtt import client as mqtt

from mqtt_service.config.config import MQTT_USERNAME, log, MQTT_PASSWORD, MQTT_HOST, MQTT_PORT, FILTER_PERM, \
    FILTER_CONN, MQTT_TOPIC
from mqtt_service.config.database import ensure_schema
from mqtt_service.services.insert_message import insert_measurements, insert_message
from mqtt_service.services.parse_payload import parse_payload, extract_ids


def main():
    ensure_schema()

    client = mqtt.Client(client_id="mqtt-service")  # paho-mqtt v1 API
    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_forever()


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        log.info("Connected to MQTT broker.")
        client.subscribe(MQTT_TOPIC, qos=1)
        log.info("Subscribed to %s", MQTT_TOPIC)
    else:
        log.error("MQTT connect failed: rc=%s", rc)


def on_message(client, userdata, msg):
    try:
        raw_text = msg.payload.decode("utf-8", errors="replace")
        log.info("Raw MQTT message on %s: %s", msg.topic, raw_text[:300])

        doc = parse_payload(msg.payload)

        user_id, conn_id, perm_id, data_src_id = extract_ids(doc)

        # Fallback: permission_id from Topic
        if not perm_id:
            perm_from_topic = __permission_from_topic(msg.topic)
            if perm_from_topic:
                perm_id = perm_from_topic

        if not __allowed(conn_id, perm_id):
            log.debug(
                "Message filtered: conn=%s perm=%s topic=%s",
                conn_id,
                perm_id,
                msg.topic,
            )
            return

        # 1) save raw data
        insert_message(
            msg.topic,
            conn_id,
            perm_id,
            doc if "_raw" not in doc else None,
            raw_text,
        )

        # 2) Save measurements – pass IDs explicitly
        doc_for_meas = doc if "_raw" not in doc else {"_raw": raw_text}
        insert_measurements(
            msg.topic,
            doc_for_meas,
            override_ids=(user_id, conn_id, perm_id, data_src_id),
        )

        log.info(
            "Stored message: topic=%s conn=%s perm=%s",
            msg.topic,
            conn_id,
            perm_id,
        )
    except Exception as e:
        log.exception("Failed to process message: %s", e)


def __allowed(connection_id: Optional[str], permission_id: Optional[str]) -> bool:
    ok_c = (FILTER_CONN is None) or (
            connection_id is not None and connection_id in FILTER_CONN
    )
    ok_p = (FILTER_PERM is None) or (
            permission_id is not None and permission_id in FILTER_PERM
    )
    return ok_c and ok_p


def __permission_from_topic(topic: str) -> Optional[str]:
    """
    Expects Topics like:
      aiida/v1/<permission_id>/data/...
    and returns the permission_id as a string, otherwise None.
    """
    parts = topic.split("/")
    if len(parts) >= 3:
        candidate = parts[2]
        try:
            return str(uuid.UUID(candidate))
        except ValueError:
            return None
    return None


if __name__ == "__main__":
    main()
