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
    "limit": 100
}

def text_de(value):
    if isinstance(value, dict):
        return value.get("de") or value.get("en") or value.get("fr") or ""
    return value or ""

def find_value(obj, possible_keys):
    if isinstance(obj, dict):
        for key in possible_keys:
            if key in obj and obj[key]:
                return obj[key]

        for value in obj.values():
            found = find_value(value, possible_keys)
            if found:
                return found

    elif isinstance(obj, list):
        for item in obj:
            found = find_value(item, possible_keys)
            if found:
                return found

    return ""

def normalize_event(event):
    title = text_de(find_value(event, ["title", "name", "eventTitle"]))
    date = find_value(event, ["startDate", "start", "date", "startTime", "begin"])
    city = text_de(find_value(event, ["city", "locationCity", "place", "town"]))
    url = find_value(event, ["url", "link", "eventUrl"])
    image = find_value(event, ["image", "imageUrl", "picture", "thumbnailUrl", "posterUrl"])
    category = text_de(find_value(event, ["category", "rubric", "type"]))

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

    # Nur Events behalten, die einen Titel haben
    events = [event for event in events if event["title"]]

    data = {
    "status_code": response.status_code,
    "count": len(events),
    "first_raw_event": events_raw[0] if events_raw else {},
    "events": events[:100]
}

except Exception as e:
    data = {
        "error": str(e)
    }

with open("events.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("events.json wurde erstellt")
