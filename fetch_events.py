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
    "limit": 10
}

try:
    response = requests.get(URL, headers=headers, params=params, timeout=30)

    data = {
        "status_code": response.status_code,
        "response": response.text[:5000]
    }

    try:
        data["json"] = response.json()
    except Exception:
        pass

except Exception as e:
    data = {
        "error": str(e)
    }

with open("events.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("events.json wurde erstellt")
