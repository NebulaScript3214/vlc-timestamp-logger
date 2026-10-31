import re
import time
import json
import base64
import datetime
import urllib.request
from pathlib import Path

VLC_BASE_URL = "http://127.0.0.1:8080/requests/status.json"
VLC_PASSWORD = "1234"
LOG_FILE = Path(__file__).resolve().parent / "vlc_timestamps.txt"
COMPLETION_THRESHOLD = 95  # Percentage required to mark a video as Completed

def format_seconds(seconds):
    return str(datetime.timedelta(seconds=int(seconds)))

def get_auth_headers():
    auth_str = base64.b64encode(f":{VLC_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {auth_str}"}

def load_log_data():
    """Reads existing log entries and extracts saved resume times in seconds."""
    lines = {}
    saved_seconds = {}
    if LOG_FILE.exists():
        for line in LOG_FILE.read_text(encoding="utf-8").splitlines():
            if " | " in line:
                name, data = line.split(" | ", 1)
                name = name.strip()
                lines[name] = data.strip()
                # Extract seconds from pattern like (2535s)
                match = re.search(r"\((\d+)s\)", data)
                if match:
                    saved_seconds[name] = int(match.group(1))
    return lines, saved_seconds

def update_txt_log(lines, video_name, raw_seconds, total_length, is_completed=False):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    duration_str = format_seconds(total_length) if total_length > 0 else "Unknown"

    if is_completed:
        lines[video_name] = f"[Completed] / {duration_str} (100%) (0s) | Updated: {now}"
    else:
        timestamp_str = format_seconds(raw_seconds)
        percent = int((raw_seconds / total_length) * 100) if total_length > 0 else 0
        lines[video_name] = (
            f"{timestamp_str} / {duration_str} ({percent}%) ({raw_seconds}s) | Updated: {now}"
        )

    output = [f"{name} | {data}" for name, data in lines.items()]
    LOG_FILE.write_text("\n".join(output) + "\n", encoding="utf-8")

def seek_vlc(seconds, headers):
    """Commands VLC to jump directly to the saved timestamp."""
    seek_url = f"{VLC_BASE_URL}?command=seek&val={int(seconds)}"
    req = urllib.request.Request(seek_url, headers=headers)
    with urllib.request.urlopen(req, timeout=2):
        pass

def monitor_vlc():
    print(f"Monitoring VLC v2.0... Saving positions to: {LOG_FILE.resolve()}")
    headers = get_auth_headers()
    lines, saved_seconds = load_log_data()

    active_video = None
    last_logged_time = {}
    completed_in_session = set()

    while True:
        try:
            req = urllib.request.Request(VLC_BASE_URL, headers=headers)
            with urllib.request.urlopen(req, timeout=2) as response:
                data = json.loads(response.read().decode("utf-8"))
                state = data.get("state")

                if state in ("playing", "paused"):
                    raw_time = int(data.get("time", 0))
                    total_length = int(data.get("length", 0))
                    info = data.get("information", {}).get("category", {}).get("meta", {})
                    filename = info.get("filename", "Unknown_Video")

                    # 1. AUTOMATIC RESUME: Trigger when a video is newly opened
                    if filename != active_video:
                        active_video = filename
                        completed_in_session.discard(filename)
                        resume_sec = saved_seconds.get(filename, 0)

                        # If video started near the beginning and has a saved spot > 10s
                        if resume_sec > 10 and raw_time < 15:
                            seek_vlc(resume_sec, headers)
                            last_logged_time[filename] = resume_sec
                            print(f"--> Auto-resumed '{filename}' at {format_seconds(resume_sec)}")
                            time.sleep(2)
                            continue

                    # 2. 95% COMPLETION DETECTION
                    if total_length > 0:
                        percent = (raw_time / total_length) * 100
                        if percent >= COMPLETION_THRESHOLD:
                            if filename not in completed_in_session:
                                update_txt_log(lines, filename, 0, total_length, is_completed=True)
                                saved_seconds[filename] = 0
                                completed_in_session.add(filename)
                                print(f"--> Marked as [Completed]: {filename} ({int(percent)}%)")
                            time.sleep(3)
                            continue

                    # 3. WATCH PERCENTAGE & PROGRESS LOGGING (Every 5 seconds of change)
                    if raw_time >= 5 and abs(raw_time - last_logged_time.get(filename, -10)) >= 5:
                        update_txt_log(lines, filename, raw_time, total_length, is_completed=False)
                        saved_seconds[filename] = raw_time
                        last_logged_time[filename] = raw_time
                        pct_str = f"{int((raw_time / total_length) * 100)}%" if total_length > 0 else ""
                        print(f"Saved: {filename} at {format_seconds(raw_time)} ({pct_str})")

                else:
                    # Reset active video when playback stops so reopening it triggers auto-resume
                    active_video = None

        except Exception:
            # VLC is closed; reset active_video so reopening VLC triggers auto-resume
            active_video = None

        time.sleep(3)

if __name__ == "__main__":
    monitor_vlc()
