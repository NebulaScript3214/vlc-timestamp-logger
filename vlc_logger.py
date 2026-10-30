import time
import json
import base64
import datetime
import urllib.request
from pathlib import Path

VLC_URL = "http://127.0.0.1:8080/requests/status.json"
VLC_PASSWORD = "1234"
LOG_FILE = Path("vlc_timestamps.txt")

def format_seconds(seconds):
    return str(datetime.timedelta(seconds=int(seconds)))

def update_txt_log(video_name, timestamp_str, raw_seconds):
    lines = {}
    if LOG_FILE.exists():
        for line in LOG_FILE.read_text(encoding="utf-8").splitlines():
            if " | " in line:
                name, data = line.split(" | ", 1)
                lines[name.strip()] = data.strip()

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines[video_name] = f"{timestamp_str} ({raw_seconds}s) | Updated: {now}"

    output = [f"{name} | {data}" for name, data in lines.items()]
    LOG_FILE.write_text("\n".join(output) + "\n", encoding="utf-8")

def monitor_vlc():
    print(f"Monitoring VLC... Saving positions to: {LOG_FILE.resolve()}")
    last_saved = {}

    auth_str = base64.b64encode(f":{VLC_PASSWORD}".encode()).decode()
    headers = {"Authorization": f"Basic {auth_str}"}

    while True:
        try:
            req = urllib.request.Request(VLC_URL, headers=headers)
            with urllib.request.urlopen(req, timeout=2) as response:
                data = json.loads(response.read().decode("utf-8"))
                state = data.get("state")

                if state in ("playing", "paused"):
                    raw_time = data.get("time", 0)
                    info = data.get("information", {}).get("category", {}).get("meta", {})
                    filename = info.get("filename", "Unknown_Video")

                    if raw_time > 0 and abs(raw_time - last_saved.get(filename, -10)) >= 5:
                        formatted_time = format_seconds(raw_time)
                        update_txt_log(filename, formatted_time, raw_time)
                        last_saved[filename] = raw_time
                        print(f"Saved: {filename} at {formatted_time}")
        except Exception:
            pass

        time.sleep(3)

if __name__ == "__main__":
    monitor_vlc()