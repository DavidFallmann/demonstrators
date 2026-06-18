import psycopg2

from mqtt_service.config.config import PG_DB, PG_USER, PG_PWD, PG_HOST, PG_PORT, DEBUG_DROP, log

DDL = """
      -- Roh-Nachrichten (optional für Debug/Trace)
      CREATE TABLE IF NOT EXISTS mqtt_messages (
                                                   ts            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                                   topic         TEXT        NOT NULL,
                                                   connection_id TEXT,
                                                   permission_id TEXT,
                                                   payload_json  JSONB,
                                                   payload_raw   TEXT
      );
      SELECT create_hypertable('mqtt_messages', 'ts', if_not_exists => TRUE);
      CREATE INDEX IF NOT EXISTS idx_mqtt_msg_conn     ON mqtt_messages (connection_id);
      CREATE INDEX IF NOT EXISTS idx_mqtt_msg_perm     ON mqtt_messages (permission_id);
      CREATE INDEX IF NOT EXISTS idx_mqtt_msg_topic_ts ON mqtt_messages (topic, ts DESC);

-- Messwerte: eine Zeile pro (ts, tag, value)
      CREATE TABLE IF NOT EXISTS mqtt_measurements (
                                                       ts             TIMESTAMPTZ      NOT NULL,
                                                       topic          TEXT             NOT NULL,
                                                       user_id        TEXT,
                                                       connection_id  TEXT,
                                                       permission_id  TEXT,
                                                       data_source_id TEXT,
                                                       asset          TEXT,
                                                       tag            TEXT,
                                                       value_numeric  DOUBLE PRECISION,
                                                       unit           TEXT,
                                                       raw_json       JSONB
      );
      SELECT create_hypertable('mqtt_measurements', 'ts', if_not_exists => TRUE);

      CREATE INDEX IF NOT EXISTS idx_meas_user_ts    ON mqtt_measurements (user_id, ts DESC);
      CREATE INDEX IF NOT EXISTS idx_meas_conn_ts    ON mqtt_measurements (connection_id, ts DESC);
      CREATE INDEX IF NOT EXISTS idx_meas_perm_ts    ON mqtt_measurements (permission_id, ts DESC);
      CREATE INDEX IF NOT EXISTS idx_meas_datasrc_ts ON mqtt_measurements (data_source_id, ts DESC);
      CREATE INDEX IF NOT EXISTS idx_meas_tag_ts     ON mqtt_measurements (tag, ts DESC);
      CREATE INDEX IF NOT EXISTS idx_meas_topic_ts   ON mqtt_measurements (topic, ts DESC); \
      """

# ------------------------- DB Helpers ----------------------
def db_conn():
    return psycopg2.connect(
        dbname=PG_DB, user=PG_USER, password=PG_PWD, host=PG_HOST, port=PG_PORT
    )


def ensure_schema():
    with db_conn() as con:
        with con.cursor() as cur:
            if DEBUG_DROP:
                log.warning("DEBUG=True: dropping mqtt_measurements & mqtt_messages …")
                cur.execute("DROP TABLE IF EXISTS mqtt_measurements CASCADE;")
                cur.execute("DROP TABLE IF EXISTS mqtt_messages CASCADE;")
                con.commit()
            cur.execute(DDL)
            con.commit()
    log.info("Timescale schema %s.", "recreated" if DEBUG_DROP else "ensured")