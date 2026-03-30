import json, os
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")

def _load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"records": []}

def _save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def record_usage(sent, recv):
    data = _load()
    data["records"].append({
        "timestamp": datetime.now().isoformat(),
        "sent": sent, "recv": recv
    })
    if len(data["records"]) > 10000:
        data["records"] = data["records"][-5000:]
    _save(data)

def get_usage_summary():
    data = _load()
    now = datetime.now()
    daily, weekly, monthly = 0, 0, 0
    for r in data["records"]:
        ts = datetime.fromisoformat(r["timestamp"])
        total = r["sent"] + r["recv"]
        if (now - ts).days < 1:
            daily += total
        if (now - ts).days < 7:
            weekly += total
        if (now - ts).days < 30:
            monthly += total
    return {
        "daily": round(daily / 1e6, 2),
        "weekly": round(weekly / 1e6, 2),
        "monthly": round(monthly / 1e6, 2)
    }

def predict_next_usage():
    data = _load()
    records = data["records"][-50:]
    if len(records) < 2:
        return "Not enough data for prediction"
    avg = sum(r["sent"] + r["recv"] for r in records) / len(records)
    return f"Predicted next interval usage: {round(avg / 1e6, 2)} MB"

def check_alerts(sent, recv, signal, conn_count, ips):
    alerts = []
    data = _load()
    records = data["records"][-100:]
    if records:
        avg = sum(r["sent"] + r["recv"] for r in records) / len(records)
        if (sent + recv) > avg * 2 and avg > 0:
            alerts.append("HIGH USAGE: Current usage is 2x above average!")
    if signal is not None and signal < 30:
        alerts.append("WEAK SIGNAL: WiFi signal below 30%!")
    if conn_count > 100:
        alerts.append("TOO MANY CONNECTIONS: Over 100 active connections!")
    private_prefixes = ("10.","172.","192.168.","127.")
    for ip_info in ips:
        ip = ip_info.get("ip","")
        if not any(ip.startswith(p) for p in private_prefixes):
            if ip_info.get("country","") in ("Unknown",):
                alerts.append(f"SUSPICIOUS IP: {ip} (country unknown)")
    return alerts
