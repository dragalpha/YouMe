# YouMe Project Progress

Date: 2026-03-13
Workspace: `c:\Users\SANTAM\Desktop\Youme`

## 1. What Was Built

- Created a local web app using Flask + yt-dlp.
- Built frontend UI for:
  - YouTube video URL input
  - Playlist URL input
  - Resolution selection (including best)
  - Best audio option (MP3 flow)
  - Download progress display
  - Downloaded files library (download + delete)
- Added backend routes for:
  - `POST /fetch_info`
  - `POST /download`
  - `GET /progress/<task_id>`
  - `GET /files`
  - `GET /download_file/<filename>`
  - `POST /delete_file`

## 2. Main Fixes Done

- Fixed ffmpeg detection issue by using local `ffmpeg.exe` when present.
- Improved download format fallback behavior for better reliability.
- Added playlist progress metadata from backend:
  - `playlist_index`
  - `playlist_count`
  - `current_title`
- Updated frontend to show playlist sequence while downloading:
  - Title prefixed like `1. Video Title`
  - Status like `Downloading 1. (1/25)`

## 3. Files Created/Updated

- `app.py`
- `templates/index.html`
- `static/style.css`
- `static/script.js`
- `requirements.txt`
- `start.bat`
- `build_exe.bat`
- `run_mobile_lan.bat`
- `PROGRESS.md` (this file)

## 4. Portable EXE Work

- Added PyInstaller-oriented runtime/resource handling in `app.py`.
- Added one-click build script: `build_exe.bat`.
- Goal: produce `dist/YouMeDownloader.exe` that is easier to share.

## 5. Hosting and Sharing Guidance Given

- Localhost use and dependency setup.
- LAN/mobile access pattern.
- Self-hosting requirements (server, firewall, reverse proxy, HTTPS).
- Friend-sharing guidance for both source mode and EXE mode.

## 6. Android Discussion Outcome

- Clarified two paths:
  - APK as client app connected to hosted backend.
  - Full on-device frontend+backend app (requires Android-native architecture with embedded Python and ffmpeg).
- Confirmed that full Android app is possible, but build/sign/test must be done with Android toolchain.

## 7. Current Status

- Web app implementation exists and includes playlist sequence visibility.
- EXE packaging support scripts are present.
- No Android Studio project has been generated yet in this workspace.

## 8. Suggested Next Steps

1. Run `build_exe.bat` and test `dist/YouMeDownloader.exe` on another Windows PC.
2. Decide Android direction:
   - WebView APK connected to hosted backend, or
   - Full embedded backend inside app.
3. If Android build is needed next, generate an Android Studio project skeleton in this workspace.

## 9. GitHub Readiness Updates (2026-03-14)

- Added `.gitignore` with practical excludes for Python cache, virtual envs, build output, downloads, and optional local binaries.
- Replaced minimal `README.md` with setup/run/build documentation suitable for GitHub visitors.
- Added GitHub Actions workflow: `.github/workflows/ci.yml` for dependency install and Python syntax check.
- Verified remote is configured:
  - `origin -> https://github.com/dragalpha/YouMe.git`

## 10. Focus Mode Expansion (2026-03-14)

- Reworked the web page into clear feature sections:
  1. Lofi + Pomodoro
  2. YT Download
- Added Pomodoro mode selection:
  - `25 / 5`
  - `50 / 10`
- Added Focus music tools inside section 1:
  - YouTube music search input and search button
  - Unified dropdown containing ambient sounds + searched songs
  - Play/pause support for selected ambient or searched track
  - Download selected searched track as MP3

## 11. Backend APIs Added For Focus Music (2026-03-14)

- `POST /music_search` for searching YouTube tracks by query.
- `POST /music_stream_url` for resolving playable audio stream URL.
- `POST /music_download` for triggering MP3 download flow from Focus section.

## 12. Section 3 Replacement (2026-03-14)

- Removed "3. Music Stream" section and its UI controls.
- Added a small Focus notepad widget in section 1:
  - Auto-save notes to localStorage
  - Clear button to reset note quickly
- Removed unused stream-player JavaScript to keep frontend clean.

## 13. Runtime Stabilization Note (2026-03-14)

- Resolved stale-process issue by stopping duplicate `python app.py` instances before restart.
- Verified live server now serves latest `templates/index.html` and `static/script.js` content.

## 14. Full Dashboard Redesign (2026-03-14)

### What changed
- **`templates/index.html`** — Completely rewritten from flat two-section layout to a sidebar dashboard shell:
  - `app-shell` flex container: `aside.sidebar` (228 px sticky) + `main.main-content`
  - 4 sidebar nav items: Focus Mode, Downloader, Library, Settings (each calls `showSection()`)
  - Mobile `header.mobile-topbar` with matching `mob-tab` buttons (hidden on desktop)
  - 4 `section.app-section` divs: `sec-focus`, `sec-downloader`, `sec-library`, `sec-settings`
  - Focus section: SVG ring timer (`circle r=84`, `stroke-dasharray:527.8`), phase badge, session pills, ambient audio card, notepad card — all original element IDs preserved
  - Library section: `div#fileList.lib-grid` renders card tiles
  - Settings section: `div.theme-picker` with 4 `theme-opt` cards for theme switching
  - Google Fonts for Inter (Batman), Nunito (Hello Kitty), Barlow Condensed (Spiderman), Orbitron (Ironman)

- **`static/style.css`** — Completely rewritten (962 lines), structured around CSS custom properties:
  - 4 theme variable blocks on `html[data-theme="..."]`: batman (dark/yellow), hello-kitty (pastel pink), spiderman (dark red/blue), ironman (dark red/gold)
  - Layout: `.app-shell`, `.sidebar`, `.main-content`, `.app-section`, `.app-section.active` (fadeSlideIn animation)
  - Timer ring: `.ring-fill` stroke-dashoffset animation via CSS transition
  - Library cards: `.lib-grid` CSS grid, `.lib-card`, `.lib-thumb`, `.lib-info`, `.lib-btn`
  - Spiderman web-grid overlay, Hello Kitty dot-pattern overlay, Ironman scan-line on lib thumbs
  - Fully responsive: single-column Focus at ≤960 px, sidebar → mobile-topbar swap at ≤768 px

- **`static/script.js`** — Targeted additions and replacements:
  - Added `showSection(name)` — switches active `.app-section` and `.nav-item`/`.mob-tab`
  - Added `setTheme(name)` + `loadSavedTheme()` — reads/writes `localStorage.youme_theme`
  - Added `RING_CIRCUMFERENCE = 527.8` and `updateTimerRing()` — animates SVG ring
  - Updated `updateFocusUI()` — calls `updateTimerRing()`, updates `#focusCycleLabel`
  - Replaced `renderFiles()` — now produces `.lib-card` tiles instead of old `.file-item` list
  - Updated `bindFocusEvents()` — removed redundant `addEventListener` calls for buttons that now use inline `onclick`
  - Added standalone `clearNotepad()` for inline `onclick` on notepad clear button
  - Updated `initApp()` — calls `loadSavedTheme()` first; library loading deferred to navigation

### No backend changes
- `app.py` unchanged — all 9 routes remain as-is

### Current Status
- Server running at `http://127.0.0.1:5000`
- Default theme: Batman (dark/yellow)
- All 4 themes switchable from Settings tab

## 15. Theme System Expansion and Asset Upgrades (2026-03-14)

### Theme image replacements completed
- Batman default wallpaper switched to `static/themes/batman-new.jpg`.
- Hello Kitty default wallpaper switched to `static/themes/hello-kitty-new.png`.
- Spiderman default wallpaper switched to `static/themes/spiderman-new-new.jpg`.
- Ironman default wallpaper switched to `static/themes/ironman-new.jpg`.

### Old asset cleanup completed
- Removed old theme images after successful replacement (`batman.png`, `hello-kitty.png`, `spiderman.png`, `spider-man-new.jpg`, `ironman.png`).

### Theme design modernization completed
- Reworked Batman, Spiderman, Hello Kitty, and Ironman into premium liquid-glass variants with per-theme accent identity.
- Added compact typography tuning for Ironman to reduce oversized/baggy visual appearance.
- Removed navbar emoji icons for cleaner premium navigation.

## 16. Custom Wallpaper UX (2026-03-14)

- Built full custom wallpaper flow in Settings:
  - File picker upload
  - Drag-and-drop upload zone
  - Crop modal using Cropper.js
  - Aspect ratio options (Screen fit, Free, 16:9, 4:3, 1:1)
- Added keyboard/overlay modal-close interactions.
- Added local persistence and clear/reset behavior for wallpaper settings.
- Made wallpaper persistence theme-aware so each theme keeps its own default/custom background state.

## 17. Full Website Scan Snapshot (2026-03-14)

### Backend route inventory verified in `app.py`
- `GET /`
- `POST /fetch_info`
- `POST /music_search`
- `POST /video_info`
- `POST /music_stream_url`
- `POST /music_download`
- `POST /download`
- `GET /progress/<task_id>`
- `GET /files`
- `GET /download_file/<filename>`
- `POST /delete_file`

### Frontend section inventory verified in `templates/index.html`
- Focus
- Downloader
- Library
- Watchlist
- Planner
- Settings

### Frontend logic inventory verified in `static/script.js`
- Section routing and theme switching
- Downloader workflow and file rendering
- Focus music search/stream support
- Wallpaper migration/loading/apply/crop-save flow

### Theme CSS inventory verified in `static/style.css`
- Theme tokens and component overrides for Batman, Hello Kitty, Spiderman, Ironman
- Active theme backgrounds mapped to latest `*-new` assets

## 18. Security Audit and Hardening (2026-03-14)

### Hardening changes implemented in `app.py`
- Added request size cap (`MAX_CONTENT_LENGTH`).
- Added security headers:
  - `X-Content-Type-Options`
  - `X-Frame-Options`
  - `Referrer-Policy`
  - `Permissions-Policy`
  - `Content-Security-Policy`
- Added URL allowlist validation for yt-dlp routes (YouTube hosts only).
- Added thread lock for download task state updates (`download_tasks_lock`).
- Changed JSON parsing to safer `request.get_json(silent=True) or {}` on key POST routes.
- Switched runtime debug mode to env-controlled (`FLASK_DEBUG=1`), disabled by default.

### Security validation results
- `pip_audit` run against `requirements.txt`: no known vulnerabilities found.
- `bandit` static scan on `app.py`: no reported findings.

### Security compatibility fix
- CSP initially broke inline `onclick`-driven UI interactions.
- Updated CSP `script-src` to include `'unsafe-inline'` to restore functionality.

## 19. Functional Validation Results (2026-03-14)

### Backend/API smoke tests passed
- Home endpoint responds with HTTP 200.
- `GET /files` returns valid payload.
- Validation/error behavior confirmed for invalid/missing input paths.
- `POST /delete_file` tested with temporary file and passed.

### Real external flow checks passed
- `POST /video_info` with real YouTube URL returned valid title.
- `POST /fetch_info` with real YouTube URL returned valid type metadata.

### Runtime stability
- Repeatedly fixed stale multi-process server state by killing duplicate Python instances and starting a clean venv server process.
- Added static asset cache-busting query version in `templates/index.html` to force latest CSS/JS load.

## 20. Time Worked Estimate

Estimated active development and debugging effort so far:
- **~11 to 14 hours total** across 2026-03-13 and 2026-03-14.

Breakdown (approximate):
- Core app + downloader/features: 3.0 to 4.0 h
- Dashboard/theme redesign and iterative UI tuning: 5.0 to 6.5 h
- Wallpaper upload/crop/drag-drop and per-theme persistence: 1.5 to 2.0 h
- Security audit + hardening + post-fix validation: 1.5 to 2.0 h

## 21. Current Status Summary

- App runs successfully from venv on `http://127.0.0.1:5000`.
- Theme system is operational with updated wallpapers and liquid-glass styling.
- Core backend routes and key user flows pass smoke tests.
- Security hardening is in place with compatibility adjustments applied.
