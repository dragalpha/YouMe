import os
import json
import threading
import uuid
import sys
import webbrowser
from flask import Flask, render_template, request, jsonify, send_from_directory
import yt_dlp


def get_resource_dir():
    """Directory where bundled resources (templates/static/ffmpeg) are available."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def get_runtime_dir():
    """Directory where user-writable files (downloads) should be stored."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


RESOURCE_DIR = get_resource_dir()
RUNTIME_DIR = get_runtime_dir()

app = Flask(
    __name__,
    template_folder=os.path.join(RESOURCE_DIR, "templates"),
    static_folder=os.path.join(RESOURCE_DIR, "static"),
)

DOWNLOAD_FOLDER = os.path.join(RUNTIME_DIR, "downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Point yt-dlp at a local ffmpeg.exe from bundled resources or runtime folder.
_resource_ffmpeg = os.path.join(RESOURCE_DIR, "ffmpeg.exe")
_runtime_ffmpeg = os.path.join(RUNTIME_DIR, "ffmpeg.exe")
FFMPEG_BINARY = _resource_ffmpeg if os.path.isfile(_resource_ffmpeg) else _runtime_ffmpeg
FFMPEG_LOCATION = os.path.dirname(FFMPEG_BINARY) if os.path.isfile(FFMPEG_BINARY) else None

# Track download progress per task ID
download_tasks = {}


def sanitize_task_id(task_id):
    """Validate task_id is a valid UUID to prevent path traversal."""
    try:
        uuid.UUID(str(task_id))
        return str(uuid.UUID(str(task_id)))
    except ValueError:
        return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/fetch_info", methods=["POST"])
def fetch_info():
    data = request.get_json()
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        **(({"ffmpeg_location": FFMPEG_LOCATION}) if FFMPEG_LOCATION else {}),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info is None:
                return jsonify({"error": "Could not retrieve video info"}), 400

        if "entries" in info:
            # Playlist
            entries = []
            for entry in info.get("entries", []):
                if entry:
                    entries.append({
                        "id": entry.get("id", ""),
                        "title": entry.get("title", "Unknown"),
                        "duration": entry.get("duration", 0),
                        "thumbnail": entry.get("thumbnail", ""),
                        "url": entry.get("webpage_url", entry.get("url", "")),
                    })
            return jsonify({
                "type": "playlist",
                "title": info.get("title", "Playlist"),
                "count": len(entries),
                "entries": entries,
            })
        else:
            # Single video — collect unique resolutions
            formats = info.get("formats", [])
            resolutions = {}
            for f in formats:
                if f.get("vcodec") != "none" and f.get("height"):
                    height = f["height"]
                    label = f"{height}p"
                    if label not in resolutions:
                        resolutions[label] = height
            sorted_res = sorted(resolutions.keys(), key=lambda x: int(x[:-1]), reverse=True)

            return jsonify({
                "type": "video",
                "title": info.get("title", "Video"),
                "duration": info.get("duration", 0),
                "thumbnail": info.get("thumbnail", ""),
                "channel": info.get("uploader", ""),
                "view_count": info.get("view_count", 0),
                "resolutions": sorted_res,
            })
    except yt_dlp.utils.DownloadError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


def progress_hook(task_id):
    def hook(d):
        task = download_tasks.get(task_id, {})
        info = d.get("info_dict") or {}
        playlist_index = info.get("playlist_index")
        playlist_count = info.get("n_entries") or info.get("playlist_count")
        current_title = info.get("title")

        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            downloaded = d.get("downloaded_bytes", 0)
            percent = (downloaded / total * 100) if total else 0
            speed = d.get("speed", 0)
            speed_str = ""
            if speed:
                if speed > 1_048_576:
                    speed_str = f"{speed / 1_048_576:.1f} MB/s"
                else:
                    speed_str = f"{speed / 1024:.1f} KB/s"
            task.update({
                "status": "downloading",
                "percent": round(percent, 1),
                "speed": speed_str,
                "filename": d.get("filename", ""),
                "playlist_index": playlist_index,
                "playlist_count": playlist_count,
                "current_title": current_title,
            })
        elif d["status"] == "finished":
            task.update({
                "status": "processing",
                "percent": 99,
                "playlist_index": playlist_index,
                "playlist_count": playlist_count,
                "current_title": current_title,
            })
        elif d["status"] == "error":
            task.update({"status": "error", "error": str(d.get("error", "Unknown error"))})
        download_tasks[task_id] = task
    return hook


def run_download(task_id, url, fmt_option, audio_only, playlist_items=None):
    """Run yt-dlp download in a background thread."""
    if audio_only:
        ydl_format = "bestaudio/best"
        postprocessors = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "320",
        }]
        outtmpl = os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s")
    else:
        if fmt_option == "best":
            # Try merged best; fall back to best single-file format if no ffmpeg
            ydl_format = "bestvideo+bestaudio/bestvideo*+bestaudio/best"
        else:
            height = fmt_option.replace("p", "")
            ydl_format = (
                f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]"
                f"/bestvideo[height<={height}]+bestaudio"
                f"/best[height<={height}]"
            )
        postprocessors = [{
            "key": "FFmpegVideoConvertor",
            "preferedformat": "mp4",
        }]
        outtmpl = os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s")

    ydl_opts = {
        "format": ydl_format,
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [progress_hook(task_id)],
        "postprocessors": postprocessors,
        "merge_output_format": "mp4",
        "noplaylist": playlist_items is None,
        **(({"ffmpeg_location": FFMPEG_LOCATION}) if FFMPEG_LOCATION else {}),
    }
    if playlist_items is not None:
        ydl_opts["noplaylist"] = False

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        download_tasks[task_id]["status"] = "done"
        download_tasks[task_id]["percent"] = 100
    except Exception as e:
        download_tasks[task_id]["status"] = "error"
        download_tasks[task_id]["error"] = str(e)


@app.route("/download", methods=["POST"])
def start_download():
    data = request.get_json()
    url = data.get("url", "").strip()
    resolution = data.get("resolution", "best")
    audio_only = data.get("audio_only", False)
    is_playlist = data.get("is_playlist", False)

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    task_id = str(uuid.uuid4())
    download_tasks[task_id] = {
        "status": "starting",
        "percent": 0,
        "speed": "",
        "is_playlist": bool(is_playlist),
    }

    thread = threading.Thread(
        target=run_download,
        args=(task_id, url, resolution, audio_only, True if is_playlist else None),
        daemon=True,
    )
    thread.start()

    return jsonify({"task_id": task_id})


@app.route("/progress/<task_id>")
def get_progress(task_id):
    safe_id = sanitize_task_id(task_id)
    if not safe_id:
        return jsonify({"error": "Invalid task ID"}), 400
    task = download_tasks.get(safe_id, {"status": "not_found"})
    return jsonify(task)


@app.route("/files")
def list_files():
    """List downloaded files."""
    files = []
    for f in os.listdir(DOWNLOAD_FOLDER):
        fpath = os.path.join(DOWNLOAD_FOLDER, f)
        if os.path.isfile(fpath):
            size = os.path.getsize(fpath)
            files.append({
                "name": f,
                "size": size,
                "size_str": format_size(size),
            })
    files.sort(key=lambda x: x["name"].lower())
    return jsonify(files)


@app.route("/download_file/<path:filename>")
def download_file(filename):
    """Serve a downloaded file safely."""
    # Prevent path traversal
    safe_name = os.path.basename(filename)
    return send_from_directory(DOWNLOAD_FOLDER, safe_name, as_attachment=True)


@app.route("/delete_file", methods=["POST"])
def delete_file():
    data = request.get_json()
    filename = os.path.basename(data.get("filename", ""))
    if not filename:
        return jsonify({"error": "No filename"}), 400
    fpath = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.isfile(fpath):
        os.remove(fpath)
        return jsonify({"success": True})
    return jsonify({"error": "File not found"}), 404


def format_size(size):
    if size >= 1_073_741_824:
        return f"{size / 1_073_741_824:.2f} GB"
    elif size >= 1_048_576:
        return f"{size / 1_048_576:.2f} MB"
    elif size >= 1024:
        return f"{size / 1024:.2f} KB"
    return f"{size} B"


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))
    url = f"http://{host}:{port}"
    print(f"\nYouMe Downloader running at: {url}\n")

    if os.getenv("OPEN_BROWSER", "1") == "1":
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    app.run(debug=False, host=host, port=port, threaded=True)
