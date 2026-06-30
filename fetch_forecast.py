#!/usr/bin/env python3
"""Fetch 7-day forecast from Open-Meteo for Abilay Norte, Oton, Iloilo and write forecast.json."""

import json
import urllib.request
from datetime import datetime, timezone, timedelta

LAT = 10.8789
LON = 122.5021
LOCATION = "Savannah Crest A, Abilay Norte, Oton, Iloilo"

# July 5–11 2026 target window (also works for any current 7-day window)
START = "2026-07-05"
END = "2026-07-11"

URL = (
    f"https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}&longitude={LON}"
    f"&daily=weathercode,temperature_2m_max,temperature_2m_min,"
    f"precipitation_probability_max,windspeed_10m_max,winddirection_10m_dominant,"
    f"uv_index_max,relative_humidity_2m_max"
    f"&timezone=Asia%2FManila"
    f"&start_date={START}&end_date={END}"
)

WMO_LABELS = {
    0: ("Sunny", "☀️"),
    1: ("Mostly Clear", "🌤️"),
    2: ("Partly Cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Foggy", "🌫️"),
    48: ("Icy Fog", "🌫️"),
    51: ("Light Drizzle", "🌦️"),
    53: ("Drizzle", "🌦️"),
    55: ("Heavy Drizzle", "🌧️"),
    61: ("Light Rain", "🌧️"),
    63: ("Rain", "🌧️"),
    65: ("Heavy Rain", "🌧️"),
    71: ("Light Snow", "❄️"),
    73: ("Snow", "❄️"),
    75: ("Heavy Snow", "❄️"),
    77: ("Snow Grains", "❄️"),
    80: ("Rain Showers", "🌧️"),
    81: ("Heavy Showers", "🌧️"),
    82: ("Violent Showers", "⛈️"),
    85: ("Snow Showers", "❄️"),
    86: ("Heavy Snow Showers", "❄️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm w/ Hail", "⛈️"),
    99: ("Thunderstorm w/ Heavy Hail", "⛈️"),
}

WIND_DIRS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
             "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]

def wind_dir_label(deg):
    if deg is None:
        return "—"
    idx = round(deg / 22.5) % 16
    return WIND_DIRS[idx]

def uv_label(uv):
    if uv is None:
        return "—"
    if uv < 3:
        return "Low"
    if uv < 6:
        return "Moderate"
    if uv < 8:
        return "High"
    if uv < 11:
        return "Very High"
    return "Extreme"

with urllib.request.urlopen(URL) as resp:
    raw = json.loads(resp.read())

daily = raw["daily"]
days = []
for i, date_str in enumerate(daily["time"]):
    code = daily["weathercode"][i]
    label, icon = WMO_LABELS.get(code, ("Unknown", "❓"))
    wind_deg = daily.get("winddirection_10m_dominant", [None]*7)[i]
    uv = daily.get("uv_index_max", [None]*7)[i]
    days.append({
        "date": date_str,
        "condition": label,
        "icon": icon,
        "temp_max": daily["temperature_2m_max"][i],
        "temp_min": daily["temperature_2m_min"][i],
        "rain_chance": daily["precipitation_probability_max"][i],
        "humidity_max": daily.get("relative_humidity_2m_max", [None]*7)[i],
        "wind_speed": daily["windspeed_10m_max"][i],
        "wind_dir": wind_dir_label(wind_deg),
        "uv_index": uv,
        "uv_label": uv_label(uv),
    })

output = {
    "generated": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M PHT"),
    "location": LOCATION,
    "days": days,
}

with open("forecast.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"forecast.json updated — {len(days)} days written.")
