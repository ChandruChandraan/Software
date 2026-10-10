/**
 * FiringSim Backend Operations Dashboard — Client Logic
 */

let ws = null;
let reconnectTimer = null;
let uptimeSeconds = 0;
let uptimeInterval = null;
let errorCount = 0;

// State caches
let currentGuns = new Map();
let maxFeedItems = 50;

document.addEventListener("DOMContentLoaded", () => {
  initDashboard();
});

async function initDashboard() {
  await fetchRestSnapshot();
  connectWebSocket();
  startUptimeTicker();
}

/**
 * Fetch initial full state from REST endpoints
 */
async function fetchRestSnapshot() {
  try {
    const [healthRes, trackerRes, gunsRes, eventsRes, logsRes] = await Promise.all([
      fetch("/api/health/details"),
      fetch("/api/tracker/status"),
      fetch("/api/tracker/guns"),
      fetch("/api/tracker/events"),
      fetch("/api/tracker/logs?limit=50"),
    ]);

    if (healthRes.ok) {
      const healthData = await healthRes.json();
      updateHealthUI(healthData);
    }

    if (trackerRes.ok) {
      const trackerData = await trackerRes.json();
      updateTrackerUI(trackerData.process, trackerData.telemetry);
    }

    if (gunsRes.ok) {
      const gunsData = await gunsRes.json();
      updateGunsTable(gunsData);
    }

    if (eventsRes.ok) {
      const eventsData = await eventsRes.json();
      renderInitialEvents(eventsData);
    }

    if (logsRes.ok) {
      const logsData = await logsRes.json();
      renderInitialLogs(logsData);
    }
  } catch (err) {
    console.error("Error fetching REST snapshot:", err);
  }
}

/**
 * WebSocket Connection & Live Updates
 */
function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/backend`;

  updateWsStatus("connecting", "Connecting...");

  try {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("[WS] Connected to backend live feed.");
      updateWsStatus("connected", "Connected");
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
      // Re-sync REST snapshot on reconnect
      fetchRestSnapshot();
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        handleWsEvent(payload);
      } catch (err) {
        console.warn("[WS] Error parsing message:", err);
      }
    };

    ws.onclose = () => {
      updateWsStatus("disconnected", "Reconnecting");
      scheduleReconnect();
    };

    ws.onerror = (err) => {
      console.error("[WS] Error:", err);
      ws.close();
    };
  } catch (err) {
    updateWsStatus("disconnected", "Offline");
    scheduleReconnect();
  }
}

function scheduleReconnect() {
  if (reconnectTimer) return;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connectWebSocket();
  }, 2000);
}

function updateWsStatus(state, label) {
  const dot = document.getElementById("ws-status-dot");
  const text = document.getElementById("header-ws-state");
  if (!dot || !text) return;

  text.textContent = label;
  dot.className = "status-dot";
  if (state === "connected") dot.classList.add("green");
  else if (state === "connecting") dot.classList.add("yellow");
  else dot.classList.add("red");
}

/**
 * Route WebSocket events to UI components
 */
function handleWsEvent(msg) {
  const topic = msg.topic;
  const data = msg.data;

  switch (topic) {
    case "shot":
      handleLiveShot(data);
      break;
    case "gun_status":
      handleLiveGunStatus(data);
      break;
    case "tracker_started":
    case "tracker_stopped":
    case "tracker_crashed":
      handleProcessLifecycle(topic, data);
      break;
    case "tracker_log":
      appendTrackerLog(data);
      break;
    case "udp_error":
      appendUdpError(data);
      break;
    default:
      break;
  }
}

/**
 * Update Health & Backend metrics
 */
function updateHealthUI(health) {
  uptimeSeconds = Math.floor(health.uptime_seconds || 0);
  document.getElementById("val-backend-uptime").textContent = `${uptimeSeconds}s`;
  document.getElementById("header-backend-uptime").textContent = formatTime(uptimeSeconds);

  if (health.udp_listener) {
    document.getElementById("val-udp-endpoint").textContent = `${health.udp_listener.host}:${health.udp_listener.port}`;
    document.getElementById("val-packets-count").textContent = health.udp_listener.packets_received;
    if (health.udp_listener.last_packet_time) {
      document.getElementById("val-last-event-time").textContent = formatTimestamp(health.udp_listener.last_packet_time);
    }
  }
}

/**
 * Update Tracker metrics & process buttons
 */
function updateTrackerUI(process, telemetry) {
  const procHeader = document.getElementById("header-tracker-proc");
  const procDot = document.getElementById("tracker-proc-dot");
  const procBadge = document.getElementById("tracker-status-badge");
  const procState = document.getElementById("val-tracker-state");
  const procPid = document.getElementById("val-tracker-pid");
  const procPath = document.getElementById("val-tracker-path");

  const btnStart = document.getElementById("btn-start-tracker");
  const btnStop = document.getElementById("btn-stop-tracker");
  const btnRestart = document.getElementById("btn-restart-tracker");

  if (process) {
    procPath.textContent = process.target_path || "—";
    procPath.title = process.target_path || "";

    if (process.running) {
      procHeader.textContent = `Running (PID ${process.pid})`;
      procDot.className = "status-dot green";
      procBadge.className = "badge badge-success";
      procBadge.textContent = "Running";
      procState.textContent = `Active (PID ${process.pid})`;
      procPid.textContent = process.pid;

      btnStart.disabled = true;
      btnStop.disabled = false;
      btnRestart.disabled = false;
    } else {
      procHeader.textContent = "Stopped";
      procDot.className = "status-dot red";
      procBadge.className = "badge badge-danger";
      procBadge.textContent = "Stopped";
      procState.textContent = process.last_error ? "Error / Exited" : "Stopped";
      procPid.textContent = "—";

      btnStart.disabled = false;
      btnStop.disabled = true;
      btnRestart.disabled = false;
    }
  }

  // Telemetry status
  updateTelemetryUI(telemetry);
}

function updateTelemetryUI(telemetry) {
  const telemHeader = document.getElementById("header-tracker-telem");
  const telemDot = document.getElementById("tracker-telem-dot");
  const telemBadge = document.getElementById("telem-badge");

  if (!telemetry || telemetry.freshness === "disconnected" || !telemetry.last_valid_event_time) {
    telemHeader.textContent = "Waiting";
    telemDot.className = "status-dot gray";
    telemBadge.className = "badge badge-gray";
    telemBadge.textContent = "Waiting for Tracker data";
    return;
  }

  if (telemetry.freshness === "connected") {
    telemHeader.textContent = "Live Telemetry";
    telemDot.className = "status-dot green";
    telemBadge.className = "badge badge-success";
    telemBadge.textContent = "Connected & Active";
  } else if (telemetry.freshness === "stale") {
    telemHeader.textContent = "Stale Telemetry";
    telemDot.className = "status-dot yellow";
    telemBadge.className = "badge badge-warning";
    telemBadge.textContent = `Stale (${telemetry.seconds_since_last_event}s ago)`;
  } else {
    telemHeader.textContent = "Disconnected";
    telemDot.className = "status-dot red";
    telemBadge.className = "badge badge-danger";
    telemBadge.textContent = "Disconnected";
  }

  if (telemetry.last_valid_event_time) {
    document.getElementById("val-last-event-time").textContent = formatTimestamp(telemetry.last_valid_event_time);
  }
}

/**
/**
 * Guns Table Management — Displays ONLY physical hardware devices
 */
function isPhysicalGun(g) {
  return g && g.connected && g.port && !g.port.startsWith("SIM-");
}

function updateGunsTable(guns) {
  currentGuns.clear();
  // Filter strictly to connected physical hardware devices
  guns.filter((g) => isPhysicalGun(g)).forEach((g) => currentGuns.set(g.gun_id, g));
  renderGuns();
}

function renderGuns() {
  const tbody = document.getElementById("guns-table-body");
  if (!tbody) return;

  const sortedGuns = Array.from(currentGuns.values())
    .filter((g) => isPhysicalGun(g))
    .sort((a, b) => a.gun_id - b.gun_id);

  if (sortedGuns.length === 0) {
    tbody.innerHTML = `<tr class="empty-row" id="empty-guns-row"><td colspan="7">No physical gun hardware connected. Waiting for USB devices...</td></tr>`;
    updateGunsCounters(0, 0, 0);
    return;
  }

  let html = "";
  let connectedCount = 0;
  let totalShots = 0;

  sortedGuns.forEach((gun) => {
    connectedCount++;
    totalShots += gun.shot_count || 0;

    const coordsStr = gun.last_shot_coords
      ? `${Math.round(gun.last_shot_coords.x)}, ${Math.round(gun.last_shot_coords.y)}`
      : "—";

    const lastSeenStr = gun.last_seen ? formatTimestamp(gun.last_seen) : "—";

    html += `
      <tr>
        <td class="font-mono"><strong>Gun ${gun.gun_id}</strong></td>
        <td>Lane ${gun.lane}</td>
        <td class="font-mono text-cyan">${gun.port || "N/A"}</td>
        <td><span class="badge badge-success">Connected</span></td>
        <td class="font-mono">${gun.shot_count || 0}</td>
        <td class="font-mono">${coordsStr}</td>
        <td class="font-mono text-muted">${lastSeenStr}</td>
      </tr>
    `;
  });

  tbody.innerHTML = html;
  updateGunsCounters(connectedCount, currentGuns.size, totalShots);
}

function updateGunsCounters(connected, total, shots) {
  const badge = document.getElementById("connected-guns-badge");
  const countText = document.getElementById("val-connected-guns-count");
  const shotsText = document.getElementById("val-total-shots-count");

  if (badge) badge.textContent = `${connected} Hardware`;
  if (countText) countText.textContent = `${connected} Physical`;
  if (shotsText) shotsText.textContent = shots;
}

/**
 * Handle Live Telemetry Events — Trigger Shots
 */
function handleLiveShot(data) {
  // Update packet count
  incrementPacketCount();

  // Update gun state
  const gun = currentGuns.get(data.gun) || {
    gun_id: data.gun,
    lane: data.lane,
    connected: true,
    shot_count: data.round,
  };
  gun.connected = true;
  gun.shot_count = data.round;
  gun.last_seen = Date.now() / 1000;
  gun.last_shot_coords = { x: data.x, y: data.y };
  currentGuns.set(data.gun, gun);
  renderGuns();

  // Prepend trigger event to live events feed
  appendFeedEvent({
    type: "shot",
    gun: data.gun,
    lane: data.lane,
    x: data.x,
    y: data.y,
    round: data.round,
    timestamp: Date.now() / 1000,
  });

  // Update last message & telemetry freshness
  document.getElementById("val-tracker-last-msg").textContent = `Trigger Shot: Gun ${data.gun} Lane ${data.lane} (Round #${data.round})`;
  updateTelemetryUI({ freshness: "connected", last_valid_event_time: Date.now() / 1000 });
}

function handleLiveGunStatus(data) {
  incrementPacketCount();

  if (!data.connected || (data.port && data.port.startsWith("SIM-"))) {
    // If device disconnected or virtual simulation: remove from fleet table
    currentGuns.delete(data.gun);
  } else {
    // If real physical hardware connected: update or add to fleet table
    const gun = currentGuns.get(data.gun) || {
      gun_id: data.gun,
      lane: data.lane,
    };
    gun.lane = data.lane;
    gun.port = data.port;
    gun.connected = true;
    gun.shot_count = Math.max(gun.shot_count || 0, data.shot_count || 0);
    gun.last_seen = Date.now() / 1000;
    currentGuns.set(data.gun, gun);
  }
  renderGuns();

  const statusLabel = data.connected ? "CONNECTED" : "DISCONNECTED";
  document.getElementById("val-tracker-last-msg").textContent = `Device: Gun ${data.gun} ${statusLabel} (${data.port || "N/A"})`;
  updateTelemetryUI({ freshness: "connected", last_valid_event_time: Date.now() / 1000 });
}

function incrementPacketCount() {
  const el = document.getElementById("val-packets-count");
  if (el) {
    const current = parseInt(el.textContent, 10) || 0;
    el.textContent = current + 1;
  }
  document.getElementById("val-last-event-time").textContent = formatTimestamp(Date.now() / 1000);
}

/**
 * Live Feed Rendering — Shows trigger events
 */
function renderInitialEvents(events) {
  const feedList = document.getElementById("events-feed-list");
  const emptyState = document.getElementById("feed-empty-state");
  if (!feedList) return;

  // Only show trigger events in the live feed
  const triggerEvents = (events || []).filter((ev) => ev.type === "shot");

  if (triggerEvents.length === 0) {
    if (emptyState) emptyState.style.display = "flex";
    return;
  }

  if (emptyState) emptyState.style.display = "none";
  feedList.innerHTML = "";
  triggerEvents.slice(0, maxFeedItems).forEach((ev) => {
    feedList.appendChild(createFeedElement(ev));
  });
}

function appendFeedEvent(ev) {
  const feedList = document.getElementById("events-feed-list");
  const emptyState = document.getElementById("feed-empty-state");
  if (!feedList) return;

  if (emptyState) emptyState.style.display = "none";

  const el = createFeedElement(ev);
  feedList.insertBefore(el, feedList.firstChild);

  // Trim overflow
  while (feedList.children.length > maxFeedItems) {
    feedList.removeChild(feedList.lastChild);
  }
}

function createFeedElement(ev) {
  const item = document.createElement("div");
  item.className = `feed-item ${ev.type}`;

  const timeStr = formatTimestamp(ev.timestamp);

  if (ev.type === "shot") {
    item.innerHTML = `
      <div class="feed-meta">
        <span class="badge badge-cyan">SHOT</span>
        <strong>Gun ${ev.gun}</strong>
        <span class="text-muted">Lane ${ev.lane}</span>
      </div>
      <div class="feed-details">
        <span>X: ${Math.round(ev.x)} Y: ${Math.round(ev.y)}</span>
        <span>Round #${ev.round}</span>
        <span class="text-muted">${timeStr}</span>
      </div>
    `;
  } else {
    const badge = ev.connected
      ? `<span class="badge badge-success">CONNECT</span>`
      : `<span class="badge badge-danger">DISCONNECT</span>`;
    item.innerHTML = `
      <div class="feed-meta">
        ${badge}
        <strong>Gun ${ev.gun}</strong>
        <span class="text-muted">Lane ${ev.lane}</span>
      </div>
      <div class="feed-details">
        <span>Port: ${ev.port || "N/A"}</span>
        <span>Shots: ${ev.shot_count || 0}</span>
        <span class="text-muted">${timeStr}</span>
      </div>
    `;
  }

  return item;
}

async function clearEventLog() {
  try {
    await fetch("/api/tracker/clear-events", { method: "POST" });
    const feedList = document.getElementById("events-feed-list");
    const emptyState = document.getElementById("feed-empty-state");
    if (feedList) feedList.innerHTML = "";
    if (emptyState) emptyState.style.display = "flex";
  } catch (err) {
    console.error("Failed to clear event log:", err);
  }
}

/**
 * Diagnostics and Process Logs
 */
function renderInitialLogs(logs) {
  const term = document.getElementById("terminal-tracker-logs");
  if (!term || !logs || logs.length === 0) return;

  term.innerHTML = "";
  logs.forEach((entry) => {
    appendLogToTerminal(term, entry);
  });
}

function appendTrackerLog(entry) {
  const term = document.getElementById("terminal-tracker-logs");
  if (!term) return;
  appendLogToTerminal(term, entry);
}

function appendLogToTerminal(term, entry) {
  const line = document.createElement("div");
  line.className = `log-line ${entry.stream || "stdout"}`;
  line.textContent = `[${formatTimestamp(entry.timestamp)}] ${entry.text}`;
  term.appendChild(line);

  // Auto-scroll
  term.scrollTop = term.scrollHeight;
}

function appendUdpError(data) {
  errorCount++;
  const badge = document.getElementById("err-count-badge");
  if (badge) badge.textContent = errorCount;

  const term = document.getElementById("terminal-udp-errors");
  if (!term) return;

  const line = document.createElement("div");
  line.className = "log-line stderr";
  line.textContent = `[${formatTimestamp(Date.now() / 1000)}] ${data.error} (raw: ${data.raw || "N/A"})`;
  term.appendChild(line);
  term.scrollTop = term.scrollHeight;
}

function switchDiagTab(tabId) {
  const tabLogs = document.getElementById("tab-tracker-logs");
  const tabErrors = document.getElementById("tab-udp-errors");
  const viewLogs = document.getElementById("view-tracker-logs");
  const viewErrors = document.getElementById("view-udp-errors");

  if (tabId === "tracker-logs") {
    tabLogs.classList.add("active");
    tabErrors.classList.remove("active");
    viewLogs.classList.add("active");
    viewErrors.classList.remove("active");
  } else {
    tabErrors.classList.add("active");
    tabLogs.classList.remove("active");
    viewErrors.classList.add("active");
    viewLogs.classList.remove("active");
  }
}

/**
 * Process Lifecycle Actions
 */
function handleProcessLifecycle(topic, data) {
  fetchRestSnapshot();
}

async function startTracker() {
  const btn = document.getElementById("btn-start-tracker");
  setButtonLoading(btn, true, "Starting...");
  try {
    const res = await fetch("/api/tracker/start", { method: "POST" });
    const data = await res.json();
    if (!res.ok) {
      alert(`Start failed: ${data.detail?.message || "Unknown error"}`);
    }
  } catch (err) {
    alert(`Start failed: ${err.message}`);
  } finally {
    setButtonLoading(btn, false, "▶ Start Tracker");
    fetchRestSnapshot();
  }
}

async function stopTracker() {
  const btn = document.getElementById("btn-stop-tracker");
  setButtonLoading(btn, true, "Stopping...");
  try {
    const res = await fetch("/api/tracker/stop", { method: "POST" });
    const data = await res.json();
    if (!res.ok) {
      alert(`Stop failed: ${data.detail?.message || "Unknown error"}`);
    }
  } catch (err) {
    alert(`Stop failed: ${err.message}`);
  } finally {
    setButtonLoading(btn, false, "⏹ Stop");
    fetchRestSnapshot();
  }
}

async function restartTracker() {
  const btn = document.getElementById("btn-restart-tracker");
  setButtonLoading(btn, true, "Restarting...");
  try {
    const res = await fetch("/api/tracker/restart", { method: "POST" });
    const data = await res.json();
    if (!res.ok) {
      alert(`Restart failed: ${data.detail?.message || "Unknown error"}`);
    }
  } catch (err) {
    alert(`Restart failed: ${err.message}`);
  } finally {
    setButtonLoading(btn, false, "↻ Restart");
    fetchRestSnapshot();
  }
}

function setButtonLoading(btn, loading, text) {
  if (!btn) return;
  btn.disabled = loading;
  btn.textContent = text;
}

/**
 * Utilities
 */
function startUptimeTicker() {
  if (uptimeInterval) clearInterval(uptimeInterval);
  uptimeInterval = setInterval(() => {
    uptimeSeconds++;
    document.getElementById("val-backend-uptime").textContent = `${uptimeSeconds}s`;
    document.getElementById("header-backend-uptime").textContent = formatTime(uptimeSeconds);
  }, 1000);
}

function formatTime(totalSeconds) {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return [hours, minutes, seconds].map((v) => String(v).padStart(2, "0")).join(":");
}

function formatTimestamp(ts) {
  if (!ts) return "—";
  const d = new Date(ts * 1000);
  return d.toTimeString().split(" ")[0];
}
