# ENTSOE

## Goal

The goal with ENTSOE integration is twofold:

- **POST Request:**  
  Send consumption data from the user to receive the emission (kg-CO₂ equivalent) from the API endpoint `/api/emission-series`.

- **GET Request:**  
  Retrieve the energy mix data from the API endpoint `/api/production-by-type`.

## Test Curls

To test if the ENTSOE Service is up and running, you can run the following `curl` command:

```bash
curl http://eddie.cosylab.at:8008/api/emission-series \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
        "zone": "AT",
        "start": "202503301200",
        "end":   "202503301400",
        "resolution": "PT15M",
        "unit": "kWh",
        "consumption": [0.10, 0.15, 0.20, 0.25, 0.30, 0.25, 0.20, 0.15]
      }'
