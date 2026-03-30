import psutil
import subprocess
import platform

def get_network_io():
    io = psutil.net_io_counters()
    return {"bytes_sent": io.bytes_sent, "bytes_recv": io.bytes_recv}

def get_top_processes(n=10):
    procs = []
    for p in psutil.process_iter(["pid","name","cpu_percent","memory_percent"]):
        try:
            info = p.info
            conns = len(p.net_connections(kind="inet"))
            procs.append({
                "pid": info["pid"],
                "name": info["name"],
                "cpu": round(info["cpu_percent"] or 0, 1),
                "memory": round(info["memory_percent"] or 0, 1),
                "connections": conns
            })
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
    procs.sort(key=lambda x: x["cpu"], reverse=True)
    return procs[:n]

def get_wifi_signal():
    if platform.system() != "Windows":
        return {"signal": None, "quality": "N/A", "ssid": "N/A"}
    try:
        result = subprocess.run(
            ["netsh","wlan","show","interfaces"],
            capture_output=True, text=True, timeout=5
        )
        signal = None
        ssid = "N/A"
        for line in result.stdout.split("\n"):
            if "Signal" in line and "%" in line:
                signal = int(line.split(":")[1].strip().replace("%",""))
            if "SSID" in line and "BSSID" not in line:
                ssid = line.split(":")[1].strip()
        quality = "Good" if signal and signal > 70 else "Medium" if signal and signal > 40 else "Poor"
        return {"signal": signal, "quality": quality, "ssid": ssid}
    except Exception:
        return {"signal": None, "quality": "N/A", "ssid": "N/A"}
