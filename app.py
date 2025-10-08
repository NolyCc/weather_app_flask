
import os
import math
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, flash
import requests

# === Config ===
OWM_API_KEY = os.getenv("OWM_API_KEY", "").strip()
if not OWM_API_KEY:
    # We'll allow the app to start; template will show a warning if key is missing.
    pass

BASE_URL = "https://api.openweathermap.org/data/2.5"

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")  # for flash messages


def fetch_json(url, params):
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.RequestException as e:
        return None, str(e)


def k_to_c(k):
    return round(k - 273.15, 1)


def build_icon_url(icon_code):
    # OWM icon CDN
    return f"https://openweathermap.org/img/wn/{icon_code}@2x.png"


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", weather=None, forecast=None, api_key_missing=(OWM_API_KEY == ""))


@app.route("/weather", methods=["POST"])
def weather():
    if not OWM_API_KEY:
        flash("Missing OWM_API_KEY. Set it in your environment before running.", "error")
        return redirect(url_for("index"))

    query = (request.form.get("query") or "").strip()
    use_geo = request.form.get("use_geo") == "1"
    want_forecast = request.form.get("want_forecast") == "1"
    lat = request.form.get("lat")
    lon = request.form.get("lon")

    params_current = {"appid": OWM_API_KEY, "units": "metric", "lang": "en"}
    params_forecast = {"appid": OWM_API_KEY, "units": "metric", "lang": "en"}

    # Build params based on input mode
    if use_geo and lat and lon:
        params_current.update({"lat": lat, "lon": lon})
        params_forecast.update({"lat": lat, "lon": lon})
        location_label = f"lat {lat}, lon {lon}"
    else:
        if not query:
            flash("Please enter a location (city, postal code, etc.) or use current location.", "error")
            return redirect(url_for("index"))
        params_current.update({"q": query})
        params_forecast.update({"q": query})
        location_label = query

    # Current weather
    weather_json, err = fetch_json(f"{BASE_URL}/weather", params_current)
    if err:
        flash(f"Failed to fetch current weather: {err}", "error")
        return redirect(url_for("index"))

    # Normalize current
    current = None
    if weather_json:
        current = {
            "location": f'{weather_json.get("name")}, {weather_json.get("sys", {}).get("country", "")}'.strip(", "),
            "coords": weather_json.get("coord", {}),
            "temp": weather_json.get("main", {}).get("temp"),
            "feels_like": weather_json.get("main", {}).get("feels_like"),
            "humidity": weather_json.get("main", {}).get("humidity"),
            "wind": weather_json.get("wind", {}).get("speed"),
            "description": (weather_json.get("weather") or [{}])[0].get("description", "").title(),
            "icon": build_icon_url((weather_json.get("weather") or [{}])[0].get("icon", "01d")),
            "time": datetime.fromtimestamp(weather_json.get("dt", 0), tz=timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M"),
        }

    # Forecast (optional)
    forecast_list = None
    if want_forecast:
        forecast_json, ferr = fetch_json(f"{BASE_URL}/forecast", params_forecast)
        if ferr:
            flash(f"Failed to fetch forecast: {ferr}", "error")
            forecast_list = None
        else:
            # OWM 5-day forecast returns 3-hour steps; pick one entry per day around 12:00 local
            by_day = {}
            for item in (forecast_json.get("list") or []):
                dt_local = datetime.fromtimestamp(item.get("dt", 0)).astimezone()
                day_key = dt_local.strftime("%Y-%m-%d")
                hour = dt_local.hour
                # Keep the time closest to 12:00
                best = by_day.get(day_key)
                if best is None or abs(hour - 12) < abs(best["hour"] - 12):
                    by_day[day_key] = {
                        "hour": hour,
                        "dt": dt_local.strftime("%Y-%m-%d %H:%M"),
                        "temp": item.get("main", {}).get("temp"),
                        "description": (item.get("weather") or [{}])[0].get("description", "").title(),
                        "icon": build_icon_url((item.get("weather") or [{}])[0].get("icon", "01d")),
                    }
            # Keep next 5 unique days (including today if present)
            forecast_list = []
            for day in sorted(by_day.keys())[:5]:
                entry = by_day[day]
                entry_out = {
                    "date": day,
                    "time": entry["dt"],
                    "temp": entry["temp"],
                    "description": entry["description"],
                    "icon": entry["icon"],
                }
                forecast_list.append(entry_out)

    return render_template(
        "index.html",
        weather=current,
        forecast=forecast_list,
        api_key_missing=False
    )


if __name__ == "__main__":
    # For local dev only
    app.run(host="0.0.0.0", port=5000, debug=True)
