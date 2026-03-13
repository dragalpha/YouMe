/* ─── State ──────────────────────────────────────────────── */
let currentType = null;          // 'video' | 'playlist'
let currentUrl = null;
let currentResolutions = [];
let selectedResolution = "best";
let isAudioOnly = false;
let activePolls = {};            // task_id → interval

/* ─── Toast ──────────────────────────────────────────────── */
let toastEl = null;
function showToast(msg, type = "") {
  if (!toastEl) {
    toastEl = document.createElement("div");
    toastEl.className = "toast";
    document.body.appendChild(toastEl);
  }
  toastEl.textContent = msg;
  toastEl.className = `toast ${type} show`;
  clearTimeout(toastEl._timer);
  toastEl._timer = setTimeout(() => {
    toastEl.classList.remove("show");
  }, 3500);
}

/* ─── Helpers ────────────────────────────────────────────── */
function formatDuration(secs) {
  if (!secs) return "--";
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = secs % 60;
  if (h) return `${h}:${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`;
  return `${m}:${String(s).padStart(2,"0")}`;
}

function formatViews(n) {
  if (!n) return "";
  if (n >= 1_000_000) return `${(n/1_000_000).toFixed(1)}M views`;
  if (n >= 1_000) return `${(n/1_000).toFixed(0)}K views`;
  return `${n} views`;
}

/* ─── Fetch Info ─────────────────────────────────────────── */
async function fetchInfo() {
  const urlInput = document.getElementById("urlInput");
  const url = urlInput.value.trim();
  if (!url) { showToast("Paste a YouTube URL first", "error"); return; }

  setBtnLoading("fetchBtn", true);
  hideElements("infoCard", "optionsCard");

  try {
    const res = await fetch("/fetch_info", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await res.json();
    if (data.error) { showToast(data.error, "error"); return; }

    currentUrl = url;
    currentType = data.type;
    renderInfo(data);
    renderOptions(data);
    showElements("infoCard", "optionsCard");
  } catch (e) {
    showToast("Network error – is the server running?", "error");
  } finally {
    setBtnLoading("fetchBtn", false);
  }
}

/* ─── Render Info Card ───────────────────────────────────── */
function renderInfo(data) {
  const box = document.getElementById("videoInfo");

  if (data.type === "video") {
    box.innerHTML = `
      <div class="thumb-wrap">
        ${data.thumbnail ? `<img src="${escHtml(data.thumbnail)}" alt="thumbnail" loading="lazy"/>` : ""}
      </div>
      <div class="video-meta">
        <div class="type-badge">VIDEO</div>
        <div class="video-title">${escHtml(data.title)}</div>
        <div class="video-sub">
          ${data.channel ? `<span class="meta-pill">📺 ${escHtml(data.channel)}</span>` : ""}
          ${data.duration ? `<span class="meta-pill">⏱ ${formatDuration(data.duration)}</span>` : ""}
          ${data.view_count ? `<span class="meta-pill">👁 ${formatViews(data.view_count)}</span>` : ""}
        </div>
      </div>`;
  } else {
    const entries = (data.entries || []).slice(0, 50);
    const listHtml = entries.map((e, i) => `
      <div class="playlist-entry">
        <span class="entry-index">${i + 1}</span>
        <span class="entry-title">${escHtml(e.title)}</span>
        ${e.duration ? `<span class="meta-pill">⏱ ${formatDuration(e.duration)}</span>` : ""}
      </div>`).join("");

    box.innerHTML = `
      <div class="video-meta" style="width:100%">
        <div class="type-badge">PLAYLIST</div>
        <div class="video-title">${escHtml(data.title)}</div>
        <div class="video-sub" style="margin-bottom:12px">
          <span class="meta-pill">📋 ${data.count} videos</span>
        </div>
        <div class="playlist-entries">${listHtml}</div>
      </div>`;
  }
}

/* ─── Render Options Card ────────────────────────────────── */
function renderOptions(data) {
  isAudioOnly = false;
  setFormat("video");

  currentResolutions = data.resolutions || [];
  const grid = document.getElementById("resGrid");
  grid.innerHTML = "";

  // Always include "Best" option
  const allRes = ["best", ...currentResolutions];
  allRes.forEach((r, i) => {
    const btn = document.createElement("button");
    btn.className = "res-btn" + (i === 0 ? " active" : "");
    btn.textContent = r === "best" ? "⭐ Best" : r;
    btn.onclick = () => selectResolution(r, btn);
    grid.appendChild(btn);
  });
  selectedResolution = "best";
}

function selectResolution(res, el) {
  document.querySelectorAll(".res-btn").forEach(b => b.classList.remove("active"));
  el.classList.add("active");
  selectedResolution = res;
}

function setFormat(type) {
  isAudioOnly = type === "audio";
  document.getElementById("videoBtn").classList.toggle("active", !isAudioOnly);
  document.getElementById("audioBtn").classList.toggle("active", isAudioOnly);
  document.getElementById("resGroup").style.display = isAudioOnly ? "none" : "";
}

/* ─── Start Download ─────────────────────────────────────── */
async function startDownload() {
  if (!currentUrl) return;

  const btn = document.getElementById("downloadBtn");
  btn.disabled = true;
  btn.textContent = "Starting…";

  try {
    const res = await fetch("/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url: currentUrl,
        resolution: selectedResolution,
        audio_only: isAudioOnly,
        is_playlist: currentType === "playlist",
      }),
    });
    const data = await res.json();
    if (data.error) { showToast(data.error, "error"); return; }

    const taskId = data.task_id;
    showElements("activeCard");
    addDownloadItem(taskId, isAudioOnly ? "🎵 Audio Download" : "🎬 Video Download");
    pollProgress(taskId);
    showToast("Download started!", "success");
  } catch (e) {
    showToast("Failed to start download", "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = "⬇ Download Now";
  }
}

/* ─── Download Item UI ───────────────────────────────────── */
function addDownloadItem(taskId, label) {
  const container = document.getElementById("activeDownloads");
  const div = document.createElement("div");
  div.className = "dl-item";
  div.id = `task-${taskId}`;
  div.innerHTML = `
    <div class="dl-header">
      <span class="dl-title" id="title-${taskId}">${escHtml(label)}</span>
      <span class="dl-status downloading" id="status-${taskId}">Starting…</span>
    </div>
    <div class="progress-bar-wrap">
      <div class="progress-bar" id="bar-${taskId}" style="width:0%"></div>
    </div>
    <div class="dl-meta">
      <span id="speed-${taskId}"></span>
      <span id="pct-${taskId}">0%</span>
    </div>`;
  container.prepend(div);
}

function updateDownloadItem(taskId, task) {
  const titleEl = document.getElementById(`title-${taskId}`);
  const statusEl = document.getElementById(`status-${taskId}`);
  const barEl = document.getElementById(`bar-${taskId}`);
  const speedEl = document.getElementById(`speed-${taskId}`);
  const pctEl = document.getElementById(`pct-${taskId}`);
  if (!statusEl) return;

  const idx = Number(task.playlist_index || 0);
  const count = Number(task.playlist_count || 0);
  const serialPrefix = idx > 0 ? `${idx}. ` : "";

  if (titleEl && task.current_title) {
    const numberedTitle = `${serialPrefix}${task.current_title}`;
    titleEl.textContent = numberedTitle;
    titleEl.title = numberedTitle;
  }

  const pct = task.percent || 0;
  barEl.style.width = pct + "%";
  pctEl.textContent = pct.toFixed(1) + "%";
  speedEl.textContent = task.speed || "";

  statusEl.className = `dl-status ${task.status}`;
  const serial = idx > 0 && count > 0 ? ` ${idx}. (${idx}/${count})` : "";

  if (task.status === "downloading") statusEl.textContent = `Downloading${serial}`;
  else if (task.status === "processing") statusEl.textContent = `Processing…${serial}`;
  else if (task.status === "done") {
    statusEl.textContent = "✓ Done";
    barEl.classList.add("done");
    loadFiles();
  }
  else if (task.status === "error") {
    statusEl.textContent = "✗ Error";
    showToast(`Download error: ${task.error || "unknown"}`, "error");
  }
}

/* ─── Poll Progress ──────────────────────────────────────── */
function pollProgress(taskId) {
  if (activePolls[taskId]) clearInterval(activePolls[taskId]);
  activePolls[taskId] = setInterval(async () => {
    try {
      const res = await fetch(`/progress/${encodeURIComponent(taskId)}`);
      const task = await res.json();
      updateDownloadItem(taskId, task);
      if (task.status === "done" || task.status === "error") {
        clearInterval(activePolls[taskId]);
        delete activePolls[taskId];
      }
    } catch (_) { /* ignore transient errors */ }
  }, 600);
}

/* ─── File Library ───────────────────────────────────────── */
async function loadFiles() {
  try {
    const res = await fetch("/files");
    const files = await res.json();
    renderFiles(files);
  } catch (e) {
    // silently ignore
  }
}

function renderFiles(files) {
  const box = document.getElementById("fileList");
  if (!files.length) {
    box.innerHTML = `<p class="empty-msg">No files yet.</p>`;
    return;
  }
  const html = files.map(f => {
    const isAudio = /\.(mp3|m4a|aac|ogg|flac|wav)$/i.test(f.name);
    const icon = isAudio ? "🎵" : "🎬";
    const safeEnc = encodeURIComponent(f.name);
    return `
      <div class="file-item">
        <span class="file-icon">${icon}</span>
        <span class="file-name" title="${escHtml(f.name)}">${escHtml(f.name)}</span>
        <span class="file-size">${escHtml(f.size_str)}</span>
        <div class="file-actions">
          <a href="/download_file/${safeEnc}" download>
            <button class="icon-btn" title="Download">⬇</button>
          </a>
          <button class="icon-btn delete" title="Delete" onclick="deleteFile(${JSON.stringify(f.name)})">🗑</button>
        </div>
      </div>`;
  }).join("");
  box.innerHTML = `<div class="file-list">${html}</div>`;
}

async function deleteFile(filename) {
  if (!confirm(`Delete "${filename}"?`)) return;
  try {
    const res = await fetch("/delete_file", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename }),
    });
    const data = await res.json();
    if (data.success) { showToast("File deleted", "success"); loadFiles(); }
    else showToast(data.error || "Delete failed", "error");
  } catch (e) {
    showToast("Network error", "error");
  }
}

/* ─── Utility ────────────────────────────────────────────── */
function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function showElements(...ids) { ids.forEach(id => document.getElementById(id)?.classList.remove("hidden")); }
function hideElements(...ids) { ids.forEach(id => document.getElementById(id)?.classList.add("hidden")); }

function setBtnLoading(id, loading) {
  const btn = document.getElementById(id);
  btn.disabled = loading;
  btn.querySelector(".btn-text").textContent = loading ? "Fetching…" : "Fetch";
  btn.querySelector(".btn-loader").classList.toggle("hidden", !loading);
}

// Allow pressing Enter in the URL input
document.getElementById("urlInput").addEventListener("keydown", e => {
  if (e.key === "Enter") fetchInfo();
});

// Load files on page load
window.addEventListener("DOMContentLoaded", loadFiles);
