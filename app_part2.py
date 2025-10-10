
import os
import sqlite3
from datetime import datetime, date, timezone
from typing import Optional, Tuple, Dict, Any, List
from flask import Flask, render_template, request, redirect, url_for, flash
import requests

OWM_API_KEY = os.getenv("OWM_API_KEY", "").strip()
BASE_URL = "https://api.openweathermap.org/data/2.5"

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")

DB_NAME = os.getenv("DB_NAME", "database.db")

# -------------- DB helpers --------------
def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            location_input TEXT NOT NULL,
            lat REAL,
            lon REAL,
            start_date TEXT,
            end_date TEXT,
            temp_summary TEXT,        -- JSON-ish string (simple)
            notes TEXT
        )
        """)

init_db()

# -------------- Utility --------------
def fetch_json(url: str, params: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.RequestException as e:
        return None, str(e)

def build_icon_url(icon_code: str) -> str:
    return f"https://openweathermap.org/img/wn/{icon_code}@2x.png"

def parse_date(s: str) -> Optional[date]:
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None

# -------------- Routes --------------
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", api_key_missing=(OWM_API_KEY == ""), weather=None, forecast=None)

@app.route("/weather", methods=["POST"])
def weather():
    if not OWM_API_KEY:
        flash("Missing OWM_API_KEY. Set it and restart.", "error")
        return redirect(url_for("index"))

    query = (request.form.get("query") or "").strip()
    use_geo = request.form.get("use_geo") == "1"
    want_forecast = request.form.get("want_forecast") == "1"
    lat = request.form.get("lat")
    lon = request.form.get("lon")
    start_date = (request.form.get("start_date") or "").strip()
    end_date = (request.form.get("end_date") or "").strip()

    # ---- validate date range (optional but checked if filled) ----
    sd = parse_date(start_date) if start_date else None
    ed = parse_date(end_date) if end_date else None
    if (start_date and not sd) or (end_date and not ed):
        flash("Invalid date format. Please use YYYY-MM-DD.", "error")
        return redirect(url_for("index"))
    if sd and ed and sd > ed:
        flash("Start date must be before or equal to End date.", "error")
        return redirect(url_for("index"))

    # ---- build params ----
    params_current = {"appid": OWM_API_KEY, "units": "metric", "lang": "en"}
    params_forecast = {"appid": OWM_API_KEY, "units": "metric", "lang": "en"}

    if use_geo and lat and lon:
        params_current.update({"lat": lat, "lon": lon})
        params_forecast.update({"lat": lat, "lon": lon})
        location_label = f"lat {lat}, lon {lon}"
    else:
        if not query:
            flash("Please enter a location or use current location.", "error")
            return redirect(url_for("index"))
        params_current.update({"q": query})
        params_forecast.update({"q": query})
        location_label = query

    # ---- current weather ----
    weather_json, err = fetch_json(f"{BASE_URL}/weather", params_current)
    if err:
        flash(f"Failed to fetch current weather: {err}", "error")
        return redirect(url_for("index"))

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
            "time": datetime.fromtimestamp(weather_json.get("dt", 0)).astimezone().strftime("%Y-%m-%d %H:%M"),
        }

    # ---- forecast (optional) ----
    forecast_list = None
    forecast_json, ferr = fetch_json(f"{BASE_URL}/forecast", params_forecast)
    if ferr:
        forecast_list = None
    else:
        # compact 5 unique days around noon
        by_day = {}
        for item in (forecast_json.get("list") or []):
            dt_local = datetime.fromtimestamp(item.get("dt", 0)).astimezone()
            day_key = dt_local.strftime("%Y-%m-%d")
            hour = dt_local.hour
            keep = by_day.get(day_key)
            if keep is None or abs(hour - 12) < abs(keep["hour"] - 12):
                by_day[day_key] = {
                    "hour": hour,
                    "dt": dt_local.strftime("%Y-%m-%d %H:%M"),
                    "temp": item.get("main", {}).get("temp"),
                    "description": (item.get("weather") or [{}])[0].get("description", "").title(),
                    "icon": build_icon_url((item.get("weather") or [{}])[0].get("icon", "01d")),
                }
        forecast_list = []
        for day in sorted(by_day.keys())[:5]:
            entry = by_day[day]
            forecast_list.append({
                "date": day,
                "time": entry["dt"],
                "temp": entry["temp"],
                "description": entry["description"],
                "icon": entry["icon"],
            })

    # ---- summarize temp in requested date range (if provided & within forecast range) ----
    temp_summary = {}
    if sd and ed and forecast_list:
        # map day->temp
        day_temp = {f["date"]: f["temp"] for f in forecast_list if f.get("temp") is not None}
        cur = sd
        collected: List[float] = []
        while cur <= ed:
            key = cur.strftime("%Y-%m-%d")
            if key in day_temp:
                collected.append(day_temp[key])
            cur = cur.fromordinal(cur.toordinal()+1)
        if collected:
            temp_summary = {
                "count": len(collected),
                "avg": round(sum(collected)/len(collected), 2),
                "min": round(min(collected), 2),
                "max": round(max(collected), 2),
                "range_note": "Based on available 5-day forecast"
            }
        else:
            temp_summary = {"count": 0, "range_note": "Date range is outside 5-day forecast window"}

    # ---- persist to DB (CREATE) ----
    with db() as conn:
        conn.execute("""
        INSERT INTO queries (created_at, location_input, lat, lon, start_date, end_date, temp_summary, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().astimezone().strftime("%Y-%m-%d %H:%M"),
            location_label,
            (current.get("coords") or {}).get("lat") if current else None,
            (current.get("coords") or {}).get("lon") if current else None,
            start_date or None,
            end_date or None,
            str(temp_summary) if temp_summary else None,
            None
        ))

    return render_template("index.html", weather=current, forecast=forecast_list, api_key_missing=False)

# -------------- CRUD pages --------------
@app.route("/history")
def history():
    with db() as conn:
        rows = conn.execute("SELECT * FROM queries ORDER BY id DESC").fetchall()
    return render_template("history.html", rows=rows)

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id: int):
    with db() as conn:
        row = conn.execute("SELECT * FROM queries WHERE id=?", (id,)).fetchone()
        if not row:
            flash("Record not found.", "error")
            return redirect(url_for("history"))
        if request.method == "POST":
            location_input = (request.form.get("location_input") or "").strip()
            notes = (request.form.get("notes") or "").strip() or None
            if not location_input:
                flash("Location cannot be empty.", "error")
                return redirect(url_for("edit", id=id))
            conn.execute("UPDATE queries SET location_input=?, notes=? WHERE id=?", (location_input, notes, id))
            flash("Record updated.", "info")
            return redirect(url_for("history"))
    return render_template("edit.html", row=row)

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id: int):
    with db() as conn:
        conn.execute("DELETE FROM queries WHERE id=?", (id,))
    flash("Record deleted.", "info")
    return redirect(url_for("history"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
