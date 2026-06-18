# Dockerfile at root
FROM python:3.11-slim

RUN apt-get update && apt-get install -y kafkacat nano mc jq tzdata cron procps

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app/

RUN pip install -e /app/common_models


RUN chmod +x /app/entrypoint_web_app.sh
RUN chmod +x /app/entrypoint_consumer.sh

# Cron Setup: Will copy the crontab into /etc/cron, give permissions and so on
COPY crontab /etc/cron.d/awattar_cron
RUN chmod 0644 /etc/cron.d/awattar_cron
RUN crontab /etc/cron.d/awattar_cron
RUN touch /var/log/cron.log


# We will override the CMD in docker-compose
CMD ["/app/entrypoint_web_app.sh"]
