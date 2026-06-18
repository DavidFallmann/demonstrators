#!/bin/sh

echo "Starting Consumer..."
exec python manage.py activate_consumer --settings=consumer.settings
