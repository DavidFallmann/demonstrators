from django.apps import AppConfig


class KafkaConsumerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'consumer.kafka_consumer'
