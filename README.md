
# Weather App — Tech Assessment 1 (Backend‑first, Flask)

A minimal backend‑first weather app for **Tech Assessment 1**. Users can enter a location (city, postal code, etc.) or use their current geolocation to get **real‑time current weather** and an optional **5‑day forecast** from OpenWeatherMap.

> Assessment requirements referenced from the provided PDF: build a weather app that accepts user input for location, shows current weather, and (to stand apart) add a 5‑day forecast and current‑location support【7†file_search】.

## Features
- Enter **city / postal code** or use **browser geolocation**
- Current weather: temperature, feels‑like, humidity, wind, description, icon, local time
- Optional **5‑day forecast** (one representative entry per day around noon)
- Simple server‑rendered UI (Jinja templates), minimal CSS
- No fancy frontend build steps

## Stack
- Python 3.9+
- Flask
- Requests
- Jinja2 (built into Flask)

## Setup

1. **Clone** and enter the folder:
   ```bash
   git clone <your-repo-url>
   cd weather_app_flask
   ```

2. **Create & activate venv (recommended):**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set your OpenWeatherMap API key:**
   - Sign up at https://openweathermap.org/api and get an API key.
   - Export env var:
     ```bash
     export OWM_API_KEY=your_key_here
     export FLASK_SECRET_KEY=anything  # optional
     ```
     On Windows (PowerShell):
     ```powershell
     setx OWM_API_KEY "your_key_here"
     setx FLASK_SECRET_KEY "anything"
     ```

5. **Run the app:**
   ```bash
   python app.py
   ```
   Open http://127.0.0.1:5000 in your browser.

## Notes
- Forecast endpoint returns 3‑hour intervals; we pick the item closest to **12:00** per day.
- If API key is missing, the app will show a warning and block queries.
- You can deploy this anywhere (Render/Heroku/Fly.io/Vercel‑Python) with the same env vars.

## Next steps (toward Part 2)
- Add a database (SQLite/Postgres) and implement CRUD for saved searches & results.
- Add error states, retries, input validation, and logs.
- Export results (CSV/JSON).
