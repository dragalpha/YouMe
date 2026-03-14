import os
import uuid
from functools import wraps
from urllib.parse import urlparse

from flask import Flask, request, jsonify
import yt_dlp


app = Flask(__name__)

WORKER_SECRET = os.getenv("WORKER_SECRET", "")
FFMPEG_LOCATION = os.getenv("FFMPEG_LOCATION", "") or None

ALLOWED_VIDEO_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
    "youtube-nocookie.com",
    "www.youtube-nocookie.com",
}


def worker_auth_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not WORKER_SECRET:
            return jsonify({"error": "WORKER_SECRET is not configured"}), 503
        incoming = request.headers.get("X-Worker-Secret", "")
        if incoming != WORKER_SECRET:
            return jsonify({"error": "Unauthorized worker request"}), 401
        return f(*args, **kwargs)

    return wrapper


def is_supported_media_url(raw_url):
    try:
        parsed = urlparse(raw_url)
        if parsed.scheme not in {"http", "https"}:
            return False
        host = (parsed.hostname or "").lower()
        return host in ALLOWED_VIDEO_HOSTS
    except Exception:
        return False


def base_ydl_opts():
    opts = {
        "quiet": True,
        "no_warnings": True,
    }
    if FFMPEG_LOCATION:
        opts["ffmpeg_location"] = FFMPEG_LOCATION
    return opts


@app.route("/healthz")
def healthz():
    return jsonify({"ok": True})


@app.route("/fetch_info", methods=["POST"])
@worker_auth_required
def fetch_info():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    if not is_supported_media_url(url):
        return jsonify({"error": "Unsupported URL. Only YouTube links are allowed."}), 400

    ydl_opts = {**base_ydl_opts(), "extract_flat": False}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if info is None:
            return jsonify({"error": "Could not retrieve video info"}), 400

        if "entries" in info:
            entries = []
            for entry in info.get("entries", []):
                if not entry:
                    continue
                entries.append(
                    {
                        "id": entry.get("id", ""),
                        "title": entry.get("title", "Unknown"),
                        "duration": entry.get("duration", 0),
                        "thumbnail": entry.get("thumbnail", ""),
                        "url": entry.get("webpage_url", entry.get("url", "")),
                    }
                )
            return jsonify(
                {
                    "type": "playlist",
                    "title": info.get("title", "Playlist"),
                    "count": len(entries),
                    "entries": entries,
                }
            )

        formats = info.get("formats", [])
        resolutions = {}
        for f in formats:
            if f.get("vcodec") != "none" and f.get("height"):
                label = f"{f['height']}p"
                if label not in resolutions:
                    resolutions[label] = f["height"]
        sorted_res = sorted(resolutions.keys(), key=lambda x: int(x[:-1]), reverse=True)

        return jsonify(
            {
                "type": "video",
                "title": info.get("title", "Video"),
                "duration": info.get("duration", 0),
                "thumbnail": info.get("thumbnail", ""),
                "channel": info.get("uploader", ""),
                "view_count": info.get("view_count", 0),
                "resolutions": sorted_res,
            }
        )
    except yt_dlp.utils.DownloadError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Worker fetch_info failed: {str(e)}"}), 500


@app.route("/music_search", methods=["POST"])
@worker_auth_required
def music_search():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    limit = int(data.get("limit", 10) or 10)
    limit = max(1, min(limit, 25))
    if not query:
        return jsonify({"error": "No query provided"}), 400

    ydl_opts = {
        **base_ydl_opts(),
        "extract_flat": True,
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)

        tracks = []
        for entry in (info or {}).get("entries", []):
            if not entry:
                continue
            track_url = entry.get("webpage_url")
            if not track_url and entry.get("id"):
                track_url = f"https://www.youtube.com/watch?v={entry.get('id')}"
            tracks.append(
                {
                    "title": entry.get("title", "Unknown"),
                    "duration": entry.get("duration", 0),
                    "uploader": entry.get("uploader", ""),
                    "thumbnail": entry.get("thumbnail", ""),
                    "url": track_url or "",
                }
            )

        return jsonify({"query": query, "count": len(tracks), "tracks": tracks})
    except Exception as e:
        return jsonify({"error": f"Worker music_search failed: {str(e)}"}), 500


@app.route("/video_info", methods=["POST"])
@worker_auth_required
def video_info():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    if not is_supported_media_url(url):
        return jsonify({"error": "Unsupported URL. Only YouTube links are allowed."}), 400

    ydl_opts = {
        **base_ydl_opts(),
        "extract_flat": True,
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            return jsonify({"error": "Could not retrieve info"}), 400

        thumbnail = info.get("thumbnail", "")
        if not thumbnail and info.get("thumbnails"):
            thumbnail = info["thumbnails"][-1].get("url", "")

        return jsonify({"title": info.get("title", "Unknown"), "thumbnail": thumbnail})
    except Exception as e:
        return jsonify({"error": f"Worker video_info failed: {str(e)}"}), 500


@app.route("/music_stream_url", methods=["POST"])
@worker_auth_required
def music_stream_url():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    if not is_supported_media_url(url):
        return jsonify({"error": "Unsupported URL. Only YouTube links are allowed."}), 400

    ydl_opts = {
        **base_ydl_opts(),
        "format": "bestaudio/best",
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            return jsonify({"error": "No stream info found"}), 404

        if "entries" in info and info.get("entries"):
            info = info["entries"][0]

        stream_url = info.get("url")
        if not stream_url:
            return jsonify({"error": "No playable stream URL found"}), 404

        return jsonify(
            {
                "stream_url": stream_url,
                "title": info.get("title", "Track"),
                "duration": info.get("duration", 0),
            }
        )
    except Exception as e:
        return jsonify({"error": f"Worker music_stream_url failed: {str(e)}"}), 500


@app.route("/music_download", methods=["POST"])
@worker_auth_required
def music_download():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    if not is_supported_media_url(url):
        return jsonify({"error": "Unsupported URL. Only YouTube links are allowed."}), 400

    ydl_opts = {
        **base_ydl_opts(),
        "format": "bestaudio/best",
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if "entries" in info and info.get("entries"):
            info = info["entries"][0]

        stream_url = info.get("url")
        if not stream_url:
            return jsonify({"error": "No playable stream URL found"}), 404

        return jsonify(
            {
                "task_id": str(uuid.uuid4()),
                "stream_url": stream_url,
                "title": info.get("title", "Track"),
                "duration": info.get("duration", 0),
            }
        )
    except Exception as e:
        return jsonify({"error": f"Worker music_download failed: {str(e)}"}), 500


@app.route("/download", methods=["POST"])
@worker_auth_required
def download():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    if not is_supported_media_url(url):
        return jsonify({"error": "Unsupported URL. Only YouTube links are allowed."}), 400

    audio_only = bool(data.get("audio_only", False))
    resolution = (data.get("resolution") or "best").strip()

    if audio_only:
        ydl_format = "bestaudio/best"
    elif resolution == "best":
        ydl_format = "bestvideo+bestaudio/bestvideo*+bestaudio/best"
    else:
        height = resolution.replace("p", "")
        ydl_format = (
            f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]"
            f"/bestvideo[height<={height}]+bestaudio"
            f"/best[height<={height}]"
        )

    ydl_opts = {
        **base_ydl_opts(),
        "format": ydl_format,
        "noplaylist": not bool(data.get("is_playlist", False)),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if "entries" in info and info.get("entries"):
            info = info["entries"][0]

        stream_url = info.get("url")
        if not stream_url:
            return jsonify({"error": "No playable stream URL found"}), 404

        return jsonify(
            {
                "task_id": str(uuid.uuid4()),
                "stream_url": stream_url,
                "title": info.get("title", "Video"),
            }
        )
    except Exception as e:
        return jsonify({"error": f"Worker download failed: {str(e)}"}), 500


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8787"))
    app.run(host=host, port=port, threaded=True)
