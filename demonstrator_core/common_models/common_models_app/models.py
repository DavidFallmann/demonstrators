
from django.db import models
from django.contrib.auth.models import User


# Custom user models 

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='extended_user')
    connection_id = models.CharField(max_length=500, unique=True, null=True, blank=True)
    street = models.CharField(max_length=250, null=True)
    number = models.IntegerField(null=True)
    postal_code = models.IntegerField(null=True)
    city = models.IntegerField(null=True)
    country = models.IntegerField(null=True)
    
    def __str__(self):
        return self.user.username
    
class UserLog(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_log')
    feedback = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"User Log for {self.user.first_name} {self.user.last_name}"
    
     
# AWATTAR model

class marketprice_data(models.Model):
    start_timestamp = models.DateTimeField()
    end_timestamp = models.DateTimeField()
    marketprice = models.DecimalField(decimal_places=2, max_digits=10)
    unit = models.CharField(max_length=50)
    
    class Meta:
        indexes = [
            models.Index(fields=['start_timestamp']),
        ]

    
# Demonstratdor models

class MeteringPoint(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    metering_point = models.CharField(max_length=255)
    connection_id = models.CharField(max_length=255)
    data_need_id = models.CharField(max_length=255)
    permission_id = models.CharField(max_length=255)

    class Meta:
        unique_together = ('user_profile', 'metering_point')

    def __str__(self):
        return f"{self.user_profile.user.username} - {self.metering_point}"


class TimeSeriesMeta(models.Model):
    metering_point = models.ForeignKey(MeteringPoint, on_delete=models.CASCADE, related_name='time_series_metas')
    start_datetime = models.DateTimeField()
    metering_interval = models.DurationField()
    unit = models.CharField(max_length=50)

    class Meta:
        indexes = [
            models.Index(fields=['start_datetime']),
        ]

    def __str__(self):
        return f"{self.metering_point.metering_point} - Start: {self.start_datetime}"


class Consumption(models.Model):
    time_series_meta = models.ForeignKey(TimeSeriesMeta, on_delete=models.CASCADE, related_name='consumptions')
    timestamp = models.DateTimeField()
    consumption_value = models.FloatField()

    class Meta:
        unique_together = ('time_series_meta', 'timestamp')
        indexes = [
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.time_series_meta.metering_point.metering_point} - {self.timestamp} - {self.consumption_value}"
    

# ENTSOE models

class EmissionData(models.Model):
    time_series_meta = models.ForeignKey(TimeSeriesMeta, on_delete=models.CASCADE, related_name='emission_records')
    timestamp = models.DateTimeField()
    emission_value = models.FloatField()
    unit = models.CharField(max_length=20, default="kgCO2eq")
    
    class Meta:
        unique_together = ('time_series_meta', 'timestamp')
        indexes = [
            models.Index(fields=['timestamp']),
        ]
    def __str__(self):
        return f"{self.time_series_meta.metering_point.metering_point} - {self.timestamp} - {self.emission_value} kgCO2eq"


# Prediction models

class PredictionData(models.Model):
    time_series_meta = models.ForeignKey(TimeSeriesMeta, on_delete=models.CASCADE, related_name='predictions')
    timestamp = models.DateTimeField()
    unit = models.CharField(max_length=20)
    prediction_value = models.FloatField()
    total_next_day=models.FloatField()

    
    class Meta:
        indexes = [
            models.Index(fields=['timestamp']),
        ]
    def __str__(self):
        return f"{self.time_series_meta.metering_point.metering_point} - {self.timestamp} - {self.prediction_value} "


# Aiida Real time Data

import uuid
from django.conf import settings
from django.db import models


# ===========================================================
# AiiDA ↔ EDDIE Real-Time Daten (bestehende SQL-Tabelle)
# ===========================================================

import uuid
from django.conf import settings
from django.db import models


class UserAiidaRealTimeData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    permission_id = models.UUIDField(db_index=True)
    timestamp = models.DateTimeField(db_index=True)
    quantity_type = models.CharField(max_length=32)
    quality = models.CharField(max_length=64)
    quantity = models.IntegerField()
    market_document_mrid = models.CharField(max_length=64)
    data_need_id = models.CharField(max_length=64)
    connection_id = models.CharField(max_length=64)
    data_source_id = models.CharField(max_length=64)
    final_customer_id = models.CharField(max_length=64)
    document_type = models.CharField(max_length=128)
    raw = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    # user_id ist integer (ForeignKey auf auth_user.id)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="user_id",
        related_name="aiida_realtime_records"
    )

    class Meta:
        db_table = "common_models_app_useraiidarealtimedata"
        managed = True
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["permission_id", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.permission_id} @ {self.timestamp} q={self.quantity}"


class UserPermission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="aiida_permissions")
    permission_id = models.UUIDField(db_index=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "permission_id")
        indexes = [models.Index(fields=["user", "permission_id"])]

    def __str__(self):
        return f"{self.user} | {self.permission_id} | verified={self.verified}"


class MqttMeasurement(models.Model):
    ts = models.DateTimeField(primary_key=True, db_column="ts")
    topic = models.TextField(db_column="topic")
    user_id = models.TextField(db_column="user_id", null=True, blank=True)
    connection_id = models.TextField(db_column="connection_id", null=True, blank=True)
    permission_id = models.TextField(db_column="permission_id", null=True, blank=True)
    data_source_id = models.TextField(db_column="data_source_id", null=True, blank=True)
    asset = models.TextField(db_column="asset", null=True, blank=True)
    tag = models.TextField(db_column="tag", null=True, blank=True)
    value_numeric = models.FloatField(db_column="value_numeric", null=True, blank=True)
    unit = models.TextField(db_column="unit", null=True, blank=True)
    raw_json = models.JSONField(db_column="raw_json", null=True, blank=True)

    class Meta:
        db_table = "mqtt_measurements"
        managed = False
        ordering = ["ts"]

