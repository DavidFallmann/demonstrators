from django.db import models

class MqttMeasurement(models.Model):
    ts = models.DateTimeField()
    topic = models.TextField()
    user_id = models.TextField(null=True)
    connection_id = models.TextField(null=True)
    permission_id = models.TextField(null=True)
    data_source_id = models.TextField(null=True)
    asset = models.TextField(null=True)
    tag = models.TextField(null=True)
    value_numeric = models.FloatField(null=True)
    unit = models.TextField(null=True)
    message_json = models.JSONField(null=True)

    class Meta:
        managed = False
        db_table = "mqtt_measurements"
        indexes = [
            models.Index(fields=("user_id", "-ts")),
            models.Index(fields=("tag", "-ts")),
        ]
