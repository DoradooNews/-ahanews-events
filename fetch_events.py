import os
import json
import requests

API_KEY = os.environ.get("EVENTFROG_API_KEY")

URL = "https://api.eventfrog.net/public/v1/events"

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

params = {
    "limit": 50
}

def pick(obj, keys, default=""):
    for key in keys:
        if isinstance(obj, dict) and key in obj and obj[key]:
            return obj[key]
    return default

def normalize_event(event):
    title = pick(event, ["title", "name", "eventTitle"])
    date = pick(event, ["startDate", "start", "date", "startTime"])
    city = pick(event, ["city", "locationCity", "place"])
    url = pick(event, ["url", "link", "eventUrl"])
    image = pick(event, ["image", "imageUrl", "picture", "thumbnailUrl"])
    category = pick(event, ["category", "rubric", "type"])

    location = pick(event, ["location", "venue"], {})
    if not city and isinstance(location, dict):
        city = pick(location, ["city", "name"])

    return {
        "title": title,
        "date": date,
        "city": city,
        "url": url,
        "image": image,
        "category": category
    }

try:
    response = requests.get(URL, headers=headers, params=params, timeout=30)
    raw = response.json()

    if isinstance(raw, list):
        events_raw = raw
    elif isinstance(raw, dict):
        events_raw = (
            raw.get("events")
            or raw.get("items")
            or raw.get("data")
            or raw.get("results")
            or []
        )
    else:
        events_raw = []

    events = [normalize_event(event) for event in events_raw if isinstance(event, dict)]

    data = {
        "status_code": response.status_code,
        "count": len(events),
        "events": events
    }

except Exception as e:
    data = {
        "error": str(e)
    }

with open("events.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("events.json wurde erstellt")
