# VLC Timestamp Logger

VLC Media Player forgets your playback resume position after opening several other files. This lightweight Python tool monitors VLC in the background and automatically records the exact timestamp of every video you watch into a clean `vlc_timestamps.txt` file.

## Features
- **Zero External Libraries:** Uses only Python's built-in standard library.
- **Automatic Saving:** Updates your progress every 5 seconds while a video is playing or paused.
- **Clean Log Format:** Keeps a single updated line per video instead of cluttering your text file.

## Setup Instructions

### Step 1: Enable VLC Web Interface
1. Open VLC and go to **Tools** - **Preferences** (`Ctrl + P`).
2. Under **Show settings** (bottom-left), select **All**.
3. Go to **Interface** - **Main interfaces** and check **Web**.
4. Expand **Main interfaces** - **Lua**, and under **Lua HTTP**, set the **Password** to `1234`.
5. Click **Save** and restart VLC.

### Step 2: Run the Script
1. Make sure [Python](https://www.python.org/downloads/) is installed on your computer.
2. Double-click `vlc_logger.py` (or run `python vlc_logger.py` in your terminal).
3. Play any video in VLC—your timestamps will automatically be saved to `vlc_timestamps.txt` in the same folder.

## Example Output (`vlc_timestamps.txt`)
```text
Lecture_04_Algorithms.mp4 | 00:42:15 (2535s) | Updated: 2026-10-31 00:15
Movie_Night_1080p.mkv | 01:18:05 (4685s) | Updated: 2026-10-31 00:20
