#!/usr/bin/env python3
"""Fetch 7-day forecast from Open-Meteo for Abilay Norte, Oton, Iloilo and write forecast.json."""

import json
import urllib.request
from datetime import datetime, timezone, timedelta

LAT = 10.8789
LON = 122.5021
LOCATION = "Savannah Crest A, Abilay Norte, Oton, Iloilo"

START = "2026-07-05"
END   = "2026-07-11"

DAILY_PARAMS = ",".join([
    "weathercode",
    "temperature_2m_max", "temperature_2m_min",
    "apparent_temperature_max", "apparent_temperature_min",
    "precipitation_probability_max", "precipitation_sum",
    "windspeed_10m_max", "winddirection_10m_dominant", "wind_gusts_10m_max",
    "uv_index_max",
    "relative_humidity_2m_max",
    "sunrise", "sunset",
    "dew_point_2m_mean",
])

# visibility and surface_pressure are hourly-only — fetch midday (hour 12) per day
HOURLY_PARAMS = "visibility,surface_pressure"

DAILY_URL = (
    f"https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}&longitude={LON}"
    f"&daily={DAILY_PARAMS}"
    f"&hourly={HOURLY_PARAMS}"
    f"&timezone=Asia%2FManila"
    f"&start_date={START}&end_date={END}"
)

WMO_LABELS = {
    0:  ("Sunny",                    "☀️"),
    1:  ("Mostly Clear",             "🌤️"),
    2:  ("Partly Cloudy",            "⛅"),
    3:  ("Overcast",                 "☁️"),
    45: ("Foggy",                    "🌫️"),
    48: ("Icy Fog",                  "🌫️"),
    51: ("Light Drizzle",            "🌦️"),
    53: ("Drizzle",                  "🌦️"),
    55: ("Heavy Drizzle",            "🌧️"),
    61: ("Light Rain",               "🌧️"),
    63: ("Rain",                     "🌧️"),
    65: ("Heavy Rain",               "🌧️"),
    71: ("Light Snow",               "❄️"),
    73: ("Snow",                     "❄️"),
    75: ("Heavy Snow",               "❄️"),
    77: ("Snow Grains",              "❄️"),
    80: ("Rain Showers",             "🌧️"),
    81: ("Heavy Showers",            "🌧️"),
    82: ("Violent Showers",          "⛈️"),
    85: ("Snow Showers",             "❄️"),
    86: ("Heavy Snow Showers",       "❄️"),
    95: ("Thunderstorm",             "⛈️"),
    96: ("Thunderstorm w/ Hail",     "⛈️"),
    99: ("Thunderstorm w/ Heavy Hail","⛈️"),
}

WIND_DIRS = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
             "S","SSW","SW","WSW","W","WNW","NW","NNW"]

def wind_dir_label(deg):
    if deg is None: return "—"
    return WIND_DIRS[round(deg / 22.5) % 16]

def uv_label(uv):
    if uv is None: return "—"
    if uv < 3:  return "Low"
    if uv < 6:  return "Moderate"
    if uv < 8:  return "High"
    if uv < 11: return "Very High"
    return "Extreme"

def visibility_label(km):
    if km is None: return "—"
    if km >= 10: return "Perfectly clear"
    if km >= 4:  return "Clear"
    if km >= 1:  return "Hazy"
    return "Fog"

def fmt_time(iso):
    """'2026-07-05T05:42' → '5:42 AM'"""
    if not iso: return "—"
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%-I:%M %p")
    except Exception:
        return iso[-5:]

# Build hourly index: date → hour-12 index
def build_hourly_index(hourly_times):
    idx = {}
    for i, t in enumerate(hourly_times):
        # t like "2026-07-05T12:00"
        if t.endswith("T12:00"):
            date = t[:10]
            idx[date] = i
    return idx

with urllib.request.urlopen(DAILY_URL) as resp:
    raw = json.loads(resp.read())

daily  = raw["daily"]
hourly = raw.get("hourly", {})
hourly_times = hourly.get("time", [])
hourly_idx   = build_hourly_index(hourly_times)

# Week-wide temp range for the range bar
all_max = [v for v in daily.get("temperature_2m_max", []) if v is not None]
all_min = [v for v in daily.get("temperature_2m_min", []) if v is not None]
week_max = max(all_max) if all_max else 40
week_min = min(all_min) if all_min else 20

days = []
for i, date_str in enumerate(daily["time"]):
    code     = daily["weathercode"][i]
    label, icon = WMO_LABELS.get(code, ("Unknown", "❓"))
    wind_deg = daily.get("winddirection_10m_dominant", [None]*7)[i]
    uv       = daily.get("uv_index_max",               [None]*7)[i]

    # Hourly midday values
    h = hourly_idx.get(date_str)
    vis_m  = hourly["visibility"][h]      if h is not None and "visibility"      in hourly else None
    pres   = hourly["surface_pressure"][h] if h is not None and "surface_pressure" in hourly else None

    vis_km = round(vis_m / 1000, 1) if vis_m is not None else None

    # Precip sum — round to 1 decimal, omit if 0
    precip_sum = daily.get("precipitation_sum", [None]*7)[i]
    if precip_sum is not None:
        precip_sum = round(precip_sum, 1)

    days.append({
        "date":         date_str,
        "condition":    label,
        "icon":         icon,
        # temps
        "temp_max":     daily["temperature_2m_max"][i],
        "temp_min":     daily["temperature_2m_min"][i],
        "feels_max":    daily.get("apparent_temperature_max", [None]*7)[i],
        "feels_min":    daily.get("apparent_temperature_min", [None]*7)[i],
        # range bar
        "week_max":     week_max,
        "week_min":     week_min,
        # precip
        "rain_chance":  daily["precipitation_probability_max"][i],
        "precip_mm":    precip_sum,
        # wind
        "wind_speed":   daily["windspeed_10m_max"][i],
        "wind_dir":     wind_dir_label(wind_deg),
        "wind_gusts":   daily.get("wind_gusts_10m_max", [None]*7)[i],
        # uv
        "uv_index":     uv,
        "uv_label":     uv_label(uv),
        # humidity + dew point
        "humidity_max": daily.get("relative_humidity_2m_max", [None]*7)[i],
        "dew_point":    daily.get("dew_point_2m_mean",         [None]*7)[i],
        # sun
        "sunrise":      fmt_time(daily.get("sunrise", [None]*7)[i]),
        "sunset":       fmt_time(daily.get("sunset",  [None]*7)[i]),
        # hourly-derived
        "visibility_km":    vis_km,
        "visibility_label": visibility_label(vis_km),
        "pressure_hpa":     round(pres, 1) if pres is not None else None,
    })

output = {
    "generated": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M PHT"),
    "location":  LOCATION,
    "days":      days,
}

with open("forecast.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"forecast.json updated — {len(days)} days, week range {week_min}–{week_max}°C.")
