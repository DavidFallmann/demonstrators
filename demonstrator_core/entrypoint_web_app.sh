#!/bin/sh

echo "Running migrations for web_app..."
python manage.py makemigrations --settings=web_app.core.settings
python manage.py migrate --settings=web_app.core.settings

echo "Collecting static files..."
python manage.py collectstatic --noinput --settings=web_app.core.settings

echo "Starting cron service..."
service cron start


tail -f /var/log/cron.log &

if pgrep cron > /dev/null; then
    echo "Cron is running"
else
    echo "Cron is not running"
fi

echo "Starting Django server for web_app..."
exec python manage.py runserver 0.0.0.0:5005 --settings=web_app.core.settings
