import os
import json
import requests

API_KEY = os.environ.get("EVENTFROG_API_KEY")

EVENTS_URL = "https://api.eventfrog.net/public/v1/events"
LOCATIONS_URL = "https://api.eventfrog.net/public/v1/locations"

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

params = {
    "limit": 1000
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

def get_image(event):
    emblem = event.get("emblemToShow")
    if isinstance(emblem, dict) and emblem.get("url"):
        return emblem.get("url")

    image = find_value(event, [
        "image",
        "imageUrl",
        "image_url",
        "picture",
        "thumbnailUrl",
        "posterUrl"
    ])

    if isinstance(image, dict):
        return image.get("url") or ""

    if isinstance(image, str) and image.startswith("http"):
        return image

    return ""

def load_locations(location_ids):
    locations = {}

    for loc_id in location_ids:
        try:
            response = requests.get(
                LOCATIONS_URL,
                headers=headers,
                params={"id": loc_id},
                timeout=20
            )

            raw = response.json()

            if isinstance(raw, list):
                location_items = raw
            elif isinstance(raw, dict):
                location_items = (
                    raw.get("locations")
                    or raw.get("items")
                    or raw.get("data")
                    or raw.get("results")
                    or [raw]
                )
            else:
                location_items = []

            for loc in location_items:
                if not isinstance(loc, dict):
                    continue

                found_id = str(
                    loc.get("id")
                    or loc.get("locationId")
                    or loc_id
                )

                city = text_de(find_value(loc, [
                    "city",
                    "town",
                    "locationCity",
                    "municipality"
                ]))

                name = text_de(find_value(loc, [
                    "name",
                    "title",
                    "venue",
                    "locationName"
                ]))

                address = text_de(find_value(loc, [
                    "address",
                    "street",
                    "streetAddress"
                ]))

                search_text = json.dumps(loc, ensure_ascii=False).lower()

                locations[found_id] = {
                    "city": city,
                    "name": name,
                    "address": address,
                    "search_text": search_text
                }

        except Exception:
            continue

    return locations

def normalize_event(event, locations):
    title = text_de(find_value(event, ["title", "name", "eventTitle"]))
    date = find_value(event, ["startDate", "start", "date", "startTime", "begin"])
    url = find_value(event, ["url", "link", "eventUrl"])
    image = get_image(event)
    category = text_de(find_value(event, ["category", "rubric", "type"]))

    location_ids = event.get("locationIds", [])
    if not isinstance(location_ids, list):
        location_ids = []

    location_text_parts = []
    city = ""

    for loc_id in location_ids:
        loc = locations.get(str(loc_id), {})
        if loc:
            if not city and loc.get("city"):
                city = loc.get("city")

            location_text_parts.append(loc.get("name", ""))
            location_text_parts.append(loc.get("city", ""))
            location_text_parts.append(loc.get("address", ""))
            location_text_parts.append(loc.get("search_text", ""))

    event_text = json.dumps(event, ensure_ascii=False).lower()
    location_text = " ".join(location_text_parts).lower()
    full_search_text = event_text + " " + location_text

    return {
        "title": title,
        "date": date,
        "city": city,
        "url": url,
        "image": image,
        "category": category,
        "debug_has_basel": "basel" in full_search_text
    }

try:
    response = requests.get(EVENTS_URL, headers=headers, params=params, timeout=30)
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

    all_location_ids = []

    for event in events_raw:
        if isinstance(event, dict):
            ids = event.get("locationIds", [])
            if isinstance(ids, list):
                all_location_ids.extend([str(i) for i in ids])

    all_location_ids = list(set(all_location_ids))
    locations = load_locations(all_location_ids)

    events = [normalize_event(event, locations) for event in events_raw if isinstance(event, dict)]
    events = [event for event in events if event["title"]]

    # Basel-Filter mit Event + Location-Daten
    events = [event for event in events if event["debug_has_basel"]]

    data = {
        "status_code": response.status_code,
        "count": len(events),
        "locations_loaded": len(locations),
        "events": events[:100]
    }

except Exception as e:
    data = {
        "error": str(e)
    }

with open("events.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("events.json wurde erstellt")
