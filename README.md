# YouMe

YouMe is a local Flask web app that downloads YouTube videos or playlists using yt-dlp.

## Features

- Single video or playlist URL support
- Resolution selection including `best`
- Audio-only MP3 flow
- Real-time progress with speed display
- Playlist sequence progress (`playlist_index`, `playlist_count`, `current_title`)
- Downloaded files library with download and delete actions

## Tech Stack

- Python 3.10+
- Flask
- yt-dlp
- ffmpeg (optional but recommended for merge and conversion)

## Project Structure

```text
.
|-- app.py
|-- requirements.txt
|-- start.bat
|-- run_mobile_lan.bat
|-- build_exe.bat
|-- static/
|-- templates/
`-- downloads/
```

## Quick Start (Windows)

1. Install Python 3.10+ and ensure it is in PATH.
2. Open a terminal in the project folder.
3. Run:

```bat
start.bat
```

4. Open:

```text
http://127.0.0.1:5000
```

## Manual Setup

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

## Mobile Over Wi-Fi (LAN)

Run:

```bat
run_mobile_lan.bat
```

Then open from your phone on the same network using your PC local IP:

```text
http://<your-local-ip>:5000
```

## Optional ffmpeg

ffmpeg improves reliability for:

- Merging video and audio streams
- MP3 extraction and conversion

You can install ffmpeg system-wide or place `ffmpeg.exe` in the project root.

## Build Portable EXE

Run:

```bat
build_exe.bat
```

Expected output:

```text
dist\YouMeDownloader.exe
```

## API Endpoints

- `POST /fetch_info`
- `POST /download`
- `GET /progress/<task_id>`
- `GET /files`
- `GET /download_file/<filename>`
- `POST /delete_file`

## Notes

- This app is intended for local/personal use.
- Respect YouTube Terms of Service and local copyright laws.
- Do not commit large binaries or downloaded media to Git.

## License

Licensed under the terms in `LICENSE`.
