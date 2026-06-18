from flask import Flask, jsonify, request
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import lightgbm as lgb
import json
from flask import Response
import logging
import time
import os, psutil
import gc


# Logging-Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()  # Ausgabe für Docker Logs
    ]
)

logger = logging.getLogger(__name__)
logger.propagate = True

app = Flask(__name__)

# Memory and CPU Logging

def log_memory_usage(note=""):
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / (1024 * 1024)  # RAM in MB
    cpu = process.cpu_percent(interval=0.1)  # kurze Messung
    logger.info(f"[Ressourcen] {note} | RAM: {mem:.2f} MB | CPU: {cpu:.1f}%")




# feature preperations
def prepare_features(data, freq='15min'):
    data['Hour'] = data.index.hour
    data['DayOfWeek'] = data.index.dayofweek
    data['IsWeekend'] = data['DayOfWeek'].isin([5, 6]).astype(int)

    lags = [1, 2, 4, 96, 192] if freq == '15min' else [1, 2, 24, 48]
    for lag in lags:
        if lag < len(data):
            data[f'Lag_{lag}'] = data['Consumption'].shift(lag)

    rolling_windows = [4, 96]
    for window in rolling_windows:
        if window < len(data):
            data[f'Rolling_Mean_{window}'] = data['Consumption'].rolling(window=window).mean()
            data[f'Rolling_Std_{window}'] = data['Consumption'].rolling(window=window).std()

    data['Diff_1'] = data['Consumption'] - data['Consumption'].shift(1)
    if len(data) > 96:  # changed: > instead of >= so 96 points is allowed
        data['Diff_96'] = data['Consumption'] - data['Consumption'].shift(96)
    data['Hour_sin'] = np.sin(2 * np.pi * data['Hour'] / 24)
    data['Hour_cos'] = np.cos(2 * np.pi * data['Hour'] / 24)

    data = data.dropna()
    if data.empty:
        raise ValueError("Insufficient data after feature preparation.")
    return data


def normalize_to_15min(data, resolution):
    values = data["consumption"]

    if resolution == "PT15M":
        return values
    elif resolution == "PT30M":
        return [v / 2.0 for v in values for _ in range(2)]
    elif resolution == "PT1H":
        return [v / 4.0 for v in values for _ in range(4)]
    elif resolution == "P1D":
        return [values[0] / 96.0 for _ in range(96)]
    else:
        raise ValueError("Unsupported resolution")


# Model Training


logger = logging.getLogger(__name__)

def train_lightgbm_model(data):
    logger.info(f"Starte Feature-Vorbereitung für {len(data)} Datenpunkte")


    start_time = time.time()

    data = prepare_features(data)
    logger.info("Feature-Vorbereitung abgeschlossen")

    X = data.drop(columns=['Consumption'])
    y = data['Consumption']

    logger.info(f"Trainiere Modell mit {X.shape[0]} Zeilen und {X.shape[1]} Features")
    logger.debug(f"Features: {list(X.columns)}")

    train_dataset = lgb.Dataset(X, label=y)
    params = {
        'objective': 'regression',
        'metric': 'mae',
        'boosting_type': 'gbdt',
        'learning_rate': 0.1,
        'num_leaves': 15,  # kleinerer Baum
        'max_depth': 4,  # Tiefe begrenzen
        'min_data_in_leaf': 10,  # weniger Overfitting, besser für RAM
        'verbose': -1
    }

    model = lgb.train(params, train_dataset, num_boost_round=100)

    duration = time.time() - start_time
    logger.info(f"Modelltraining abgeschlossen in {duration:.2f} Sekunden")

    return model, data



@app.route('/predict', methods=['POST'])
def predict():
    logger.info("POST /predict aufgerufen")
    start_request = time.time()
    data = request.get_json()
    logger.info(f"Eingehende Daten empfangen: {list(data.keys()) if isinstance(data, dict) else 'Kein Dict'}")
    log_memory_usage("Nach Eingang der Anfrage")

    raw_resolution = data["resolution"]
    try:
        data["consumption"] = normalize_to_15min(data, raw_resolution)
        logger.info(
            f"Originalauflösung: {raw_resolution} | Nach Umrechnung {len(data['consumption'])} Werte à 15 Minuten")
        data["resolution"] = "PT15M"  # Standardintern
    except Exception as e:
        logger.warning(f"Ungültige Auflösung: {raw_resolution}")
        return Response(json.dumps({"error": "Unsupported resolution"}), mimetype='application/json'), 400

    if "consumption" in data:
        try:
            start_time = pd.to_datetime(data['start'], format='%Y%m%d%H%M')
            resolution = data['resolution']

            if resolution.startswith("PT"):
                resolution_value = int(''.join(filter(str.isdigit, resolution)))
                resolution_timedelta = pd.Timedelta(minutes=resolution_value)
                logger.info(f"Auflösung erkannt: {resolution_value} Minuten")
            else:
                logger.warning("Ungültige Auflösungsangabe")
                return Response(json.dumps({"error": "Unsupported resolution format"}), mimetype='application/json'), 400

            timestamps = pd.date_range(start=start_time, periods=len(data['consumption']), freq=resolution_timedelta)
            historical_data = pd.DataFrame({
                'Datetime': timestamps,
                'Consumption': data['consumption']
            }).set_index('Datetime')
        except Exception as e:
            logger.exception(f"Fehler beim Parsen der Eingabedaten: {str(e)}")
            return Response(json.dumps({"error": "Invalid input data format"}), mimetype='application/json'), 400
    else:
        logger.warning("Eingabe ohne 'consumption'-Feld")
        return Response(json.dumps({"error": "Unrecognized data format"}), mimetype='application/json'), 400

    historical_data = historical_data.asfreq('15min').ffill()
    logger.info("Datenvorbereitung abgeschlossen (asfreq + ffill)")

    try:
        model, prepared_data = train_lightgbm_model(historical_data)
        logger.info("Modell erfolgreich trainiert")
    except ValueError as e:
        logger.error(f"Fehler beim Modelltraining: {str(e)}")
        return Response(json.dumps({"error": str(e)}), mimetype='application/json'), 400

    last_day = prepared_data[-96:]
    if last_day.empty:
        logger.warning("Nicht genügend Daten für Vorhersage")
        return Response(json.dumps({"error": "Not enough data to predict the next day."}), mimetype='application/json'), 400

    logger.info("Beginne mit Vorhersage")
    X_next_day = last_day.drop(columns=['Consumption'])
    predictions_next_day = model.predict(X_next_day)

    if len(predictions_next_day) < 96:
        pad = 96 - len(predictions_next_day)
        predictions_next_day = np.append(predictions_next_day, [predictions_next_day[-1]] * pad)
        logger.info(f"Vorhersage aufgefüllt um {pad} Werte")

    forecast_index = pd.date_range(start=last_day.index[-1] + pd.Timedelta(minutes=15),
                                   periods=len(predictions_next_day),
                                   freq='15min')

    quarter_hourly_predictions = {
        str(timestamp): value for timestamp, value in zip(forecast_index, predictions_next_day)
    }

    hourly_predictions = {}
    for hour, group in pd.DataFrame({"value": predictions_next_day}, index=forecast_index).resample('H'):
        hourly_predictions[hour.strftime('%Y-%m-%d %H:%M:%S')] = group['value'].sum()

    total_consumption_next_day = np.sum(predictions_next_day)
    logger.info(f"Vorhersage abgeschlossen | Gesamtverbrauch: {total_consumption_next_day:.2f} kWh")
    log_memory_usage("Nach Vorhersage")

    formatted_response = {
        "zone": data.get("zone"),
        "start": data.get("start"),
        "end": data.get("end"),
        "unit": data.get("unit"),
        "resolution": data.get("resolution"),
        "consumption": {
            "quarter_hourly": quarter_hourly_predictions,
            "hourly": hourly_predictions,
            "total": total_consumption_next_day
        }
    }

    duration = time.time() - start_request
    logger.info(f"Anfrageverarbeitung abgeschlossen in {duration:.2f} Sekunden")
    return Response(json.dumps(formatted_response, indent=4), mimetype='application/json')





#if __name__ == '__main__':
#    app.run(debug=True, host='0.0.0.0', port=5001)
