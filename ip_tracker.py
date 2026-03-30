import psutil
import requests

_cache = {}

def get_active_connections(limit=10):
    conns = []
    seen = set()
    for c in psutil.net_connections(kind="inet"):
        if c.status == "ESTABLISHED" and c.raddr:
            ip = c.raddr.ip
            if ip.startswith("127.") or ip.startswith("0.") or ip in seen:
                continue
            seen.add(ip)
            country = _get_country(ip)
            conns.append({
                "ip": ip,
                "port": c.raddr.port,
                "status": c.status,
                "country": country
            })
            if len(conns) >= limit:
                break
    return conns

def _get_country(ip):
    if ip in _cache:
        return _cache[ip]
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=country", timeout=3)
        country = r.json().get("country", "Unknown")
    except Exception:
        country = "Unknown"
    _cache[ip] = country
    return country
