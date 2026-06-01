from fastapi import FastAPI
from datetime import datetime, timedelta
import pytz

app = FastAPI()


@app.get("/ping")
def ping():
    return "PONG!"


@app.get("/fake/worldclock/api/json/utc/now")
def get_current_utc_time():
    now = datetime.now(pytz.utc)

    response = {
        "$id": "1",
        "currentDateTime": now.strftime("%Y-%m-%dT%H:%MZ"),
        "utcOffset": "00:00:00",
        "isDayLightSavingsTime": False,
        "dayOfTheWeek": now.strftime("%A"),
        "timeZoneName": "UTC",
        "currentFileTime": int(now.timestamp() * 10**7),
        "ordinalDate": now.strftime("%Y-%j"),
        "serviceResponse": None,
    }

    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=16001)

    # для запуска сервера
    # pip install -r requirements.txt
    # python test_services\service_fake_worldclockapi.py
    # для проверки работоспособности curl http://127.0.0.1:16001/ping
    # curl http://127.0.0.1:16001/fake/worldclockapi/api/json/utc/now
