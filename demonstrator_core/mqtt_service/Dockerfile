FROM python:3.11-slim

WORKDIR /app

# Dependencies install
COPY mqtt_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# copy code
COPY mqtt_service /app/mqtt_service

# unprivilege user
RUN useradd -ms /bin/bash appuser
USER appuser

ENTRYPOINT ["/app/mqtt_service/entrypoint_mqtt.sh"]
