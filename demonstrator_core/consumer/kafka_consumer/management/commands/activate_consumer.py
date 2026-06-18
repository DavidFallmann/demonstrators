import json
import logging.config
import os
import xml.etree.ElementTree as ET

from django.core.management.base import BaseCommand
from kafka import KafkaConsumer

from consumer.kafka_consumer.processing.json_processor import process_data_json
from consumer.kafka_consumer.processing.xml_processor import process_data_xml
from web_app.core.settings import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


class Command(BaseCommand):

    SASL_USERNAME = os.environ.get("SASL_USERNAME")
    SASL_PASSWORD = os.environ.get("SASL_PASSWORD")
    CG_ID = os.environ.get("KAFKA_CONSUMER_GROUP_ID")
    BOOTSTRAP_SERVERS = os.environ.get("BOOTSTRAP_SERVERS")

    help = 'Consumes messages from Kafka and processes data accordingly.'

    def decode_json(self, msg_bytes):
        try:
            return json.loads(msg_bytes.decode('utf-8'))
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.WARNING(f"Skipping invalid JSON message: {e}"))
            return None

    def decode_xml(self, msg_bytes):
        try:
            text = msg_bytes.decode('utf-8').strip()
            root = ET.fromstring(text)
            return root
        except ET.ParseError as e:
            self.stdout.write(self.style.WARNING(f"Skipping invalid XML message: {e}"))
            return None

    def decode_message(self, msg_bytes):
        data_json = self.decode_json(msg_bytes)
        if data_json is not None:
            return data_json, 'json'
        data_xml = self.decode_xml(msg_bytes)
        if data_xml is not None:
            return data_xml, 'xml'
        return None, None

    def handle(self, *args, **options):
        cafile_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'CARoot.pem')

        self.stdout.write(self.style.SUCCESS("Starting Kafka consumer..."))

        while True:
            try:
                consumer = KafkaConsumer(
                    'ep.eddie-demo-univie.cim_0_82.validated-historical-data-md',
                    bootstrap_servers=self.BOOTSTRAP_SERVERS,
                    group_id=self.CG_ID,
                    client_id='univie-kafka-client',
                    security_protocol='SASL_SSL',
                    ssl_cafile=cafile_path,
                    sasl_mechanism="SCRAM-SHA-512",
                    sasl_plain_username=self.SASL_USERNAME,
                    sasl_plain_password=self.SASL_PASSWORD,
                    value_deserializer=None,
                    auto_offset_reset='earliest',
                    max_poll_interval_ms=300000   # e.g. 5 minutes
                )

                self.stdout.write(self.style.SUCCESS("Kafka consumer connected. Listening for messages..."))

                for msg in consumer:
                    self.stdout.write(
                        f"Raw message received (topic={msg.topic}, partition={msg.partition}, offset={msg.offset}):\n"
                        # f"{msg.value!r}\n"
                    )
                    data, data_type = self.decode_message(msg.value)
                    if data is None:
                        self.stdout.write(self.style.WARNING("Skipping unknown message format."))
                        continue

                    if data_type == 'json':
                        # Call the JSON processing function
                        logger.info(f"data type is {data_type}")
                        process_data_json(data)
                    elif data_type == 'xml':
                        # Call the XML processing function
                        logger.info(f"data type is {data_type}")
                        process_data_xml(data)
                    else:
                        logger.info(f"data type is: {data_type}")
                        logger.error("Data in Wrong Format")



            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error in Kafka consumer loop: {str(e)}"))
                self.stdout.write("Attempting to restart consumer in 5 seconds...")
                import time
                time.sleep(5)
            finally:
                try:
                    consumer.close()
                except Exception:
                    pass
