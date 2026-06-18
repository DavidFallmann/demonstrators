--> Von alten Rep übernommen - muss angepasst werden

## About AWATTAR API

Unser Datenfeed stellt über eine definierte Web-Schnittstelle die Börsenpreise für den nächsten Tag zur Verfügung. Es handelt sich dabei um die Daten der EPEX Spot ® Strombörse, die jeden Tag um 14:00 Uhr für den nächsten Tag aktualisiert werden.
- https://www.awattar.at/services/api 


## Activate AWATTAR API

To manually activate, run: `python manage.py activate_awattar_api`

This Command is beeing excecuted in the `entrypoint.sh` (root) script within the docker file and triggered ....


## Structure of the JSON response

```
{
  "object": "list",
  "data": [
    {
      "start_timestamp": 1722517200000,
      "end_timestamp": 1722520800000,
      "marketprice": 71.22,
      "unit": "Eur/MWh"
    },
    {
      "start_timestamp": 1722520800000,
      "end_timestamp": 1722524400000,
      "marketprice": 77.39,
      "unit": "Eur/MWh"
    },
   ...
  ],
  "url": "/de/v1/marketdata"
}

```

## Timestamp Format

1. Data coming from AWATTAR API are formated according to `Milliseconds - Unix epoch`.
2. They are then being converted from `milliseconds` to `seconds`,
3. and from seconds to pythons `datetime objects in UTC`.
4. Then, the `datetime objects` are converted to `timestamptz` (UTC time with timezone), which is the native timescaledb format.


