
# Weather App — Tech Assessment 1 (Backend‑first, Flask)

## Features
- Enter **city / postal code** or use **browser geolocation**
- Current weather: temperature, feels‑like, humidity, wind, description, icon, local time
- Optional **5‑day forecast** (one representative entry per day around noon)

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

2. **Create & activate venv:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set OpenWeatherMap API key:**
   - Sign up at https://openweathermap.org/api and get an API key.
   - Export env var:
     ```bash
     export OWM_API_KEY=your_key_here
     export FLASK_SECRET_KEY=anything  
     ```

5. **Run the app:**
   ```bash
   python app.py
   ```
   Open http://127.0.0.1:5000 in browser.

6. **Part 2**
   - Since the API that provides extended weather forecasts requires payment, I decided to continue using the same free API from Part 1 and simply add a new request function for additional data.


