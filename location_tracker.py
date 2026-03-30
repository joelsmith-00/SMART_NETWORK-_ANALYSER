import json, os

SIGNAL_MAP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "signal_map.json")

def _load():
    if os.path.exists(SIGNAL_MAP_FILE):
        with open(SIGNAL_MAP_FILE, "r") as f:
            return json.load(f)
    return {"locations": []}

def _save(data):
    with open(SIGNAL_MAP_FILE, "w") as f:
        json.dump(data, f, indent=2)

def save_location(name, signal):
    data = _load()
    data["locations"].append({"name": name, "signal": signal})
    _save(data)

def get_locations():
    return _load().get("locations", [])
