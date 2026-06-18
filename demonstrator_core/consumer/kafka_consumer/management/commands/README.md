# Kafka Consumer for Data Processing

This Django management command is the core part of the `consumer micorservice`. It continuously consumes messages from a Kafka topic and processes the data according to its format (JSON or XML).

## Overview

- **Kafka Connection:** Connects to a Kafka cluster using SASL_SSL authentication.
- **Message Consumption:** Subscribes to the `validated-historical-data` topic and listens for incoming messages.
- **Message Decoding:**  
  - **JSON:** Attempts to decode the message as JSON.
  - **XML:** If JSON decoding fails, it tries to decode as XML.
- **Data Processing:**  
  - JSON messages are processed by the `process_data_json` function located at `/consumer/processing/json_processor.py`
  - XML messages are processed by the `process_data_xml` function located at `/consumer/processing/json_processor.py`
- **Error Handling:**  
  - Utilizes an infinite loop (`while True:`) to keep the consumer running.
  - In case of an exception, logs the error, waits 5 seconds, and then restarts the consumer.
  - Ensures proper cleanup by closing the consumer connection on every iteration.

## Usage

Run the consumer as a Django management command:

```bash
python manage.py activate_consumer.py


