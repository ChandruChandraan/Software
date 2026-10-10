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
// Strict live session shot counts — initialized to 0, never restored from storage or cached state
let sessionShotCounts = new Map();
let maxFeedItems = 50;

let sessionStart = Date.now();

// Scenario Management State
let availableScenarios = [];
let selectedScenarioId = "";
let currentScenarioName = "Indoor Shooting Range";
let currentRequestId = "—";
let isScenarioRequestPending = false;

// Purge any storage immediately upon script load
try {
  localStorage.clear();
  sessionStorage.clear();
} catch (e) {}

document.addEventListener("DOMContentLoaded", () => {
  initDashboard();
});

async function initDashboard() {
  // 1. Purge any cached browser storage
  try {
    localStorage.clear();
    sessionStorage.clear();
  } catch (e) {}

  // 2. Immediately update UI to display 0 on fresh launch
  sessionShotCounts.clear();
  currentGuns.clear();
  updateGunsCounters(0, 0, 0);
  resetLocalShotCounters();

  startCockpitClock();
  initSidebarNav();
  runLaunchSplashSequence();

  // 3. Reset backend shots to guarantee previous session values (like 59/70) are wiped
  await resetBackendShots();
  await fetchRestSnapshot();
  await loadScenarios();
  await fetchActiveScenarioStatus();
  connectWebSocket();
  startUptimeTicker();
}

/**
 * Shot Counter Resets — Initializes Gun Fire Shots to 0 on launch & manual resets
 */
function resetLocalShotCounters() {
  try {
    localStorage.clear();
    sessionStorage.clear();
  } catch (e) {}

  sessionShotCounts.clear();
  currentGuns.forEach((gun) => {
    gun.shot_count = 0;
    gun.last_shot_coords = null;
    gun.last_shot_time = null;
    sessionShotCounts.set(gun.gun_id, 0);
  });
  const connectedCount = Array.from(currentGuns.values()).filter((g) => isPhysicalGun(g)).length;
  updateGunsCounters(connectedCount, currentGuns.size, 0);
  renderGuns();

  const emptyState = document.getElementById("feed-empty-state");
  const feedList = document.getElementById("events-feed-list");
  if (feedList) feedList.innerHTML = "";
  if (emptyState) emptyState.style.display = "flex";
}

async function resetBackendShots() {
  try {
    const res = await fetch("/api/tracker/reset-shots", { method: "POST" });
    if (res.ok) {
      resetLocalShotCounters();
    }
  } catch (err) {
    console.warn("[Reset] Could not reset backend shots:", err);
  }
}

async function resetShotCounters() {
  resetLocalShotCounters();
  await resetBackendShots();
  showToast("Shot counts have been reset to zero", "success");
}

function initSidebarNav() {
  const navItems = document.querySelectorAll(".sidebar-nav .nav-item");
  navItems.forEach((item) => {
    item.addEventListener("click", () => {
      navItems.forEach((i) => i.classList.remove("active"));
      item.classList.add("active");
    });
  });
}

/**
 * Launch Splash Screen Sequence
 */
function runLaunchSplashSequence() {
  const progressBar = document.getElementById("splash-progress-bar");
  const logText = document.getElementById("splash-log-text");
  const splash = document.getElementById("launch-splash-screen");

  const steps = [
    { pct: 25, msg: "[1/4] Starting communication link..." },
    { pct: 55, msg: "[2/4] Connecting screens..." },
    { pct: 80, msg: "[3/4] Starting 3D simulation and target screen..." },
    { pct: 100, msg: "[4/4] All systems ready!" },
  ];

  let stepIdx = 0;
  const interval = setInterval(() => {
    if (stepIdx < steps.length) {
      const s = steps[stepIdx];
      if (progressBar) progressBar.style.width = `${s.pct}%`;
      if (logText) logText.textContent = s.msg;
      stepIdx++;
    } else {
      clearInterval(interval);
      setTimeout(() => {
        if (splash) {
          splash.classList.add("fade-out");
          setTimeout(() => {
            splash.style.display = "none";
          }, 600);
        }
      }, 350);
    }
  }, 260);
}

/**
 * Digital Cockpit Clock
 */
function startCockpitClock() {
  const clockEl = document.getElementById("header-real-time");
  const sessionEl = document.getElementById("header-session-time");

  function tick() {
    const now = new Date();
    if (clockEl) {
      clockEl.textContent = now.toTimeString().split(" ")[0];
    }
    if (sessionEl) {
      const elapsedSec = Math.floor((Date.now() - sessionStart) / 1000);
      const h = String(Math.floor(elapsedSec / 3600)).padStart(2, "0");
      const m = String(Math.floor((elapsedSec % 3600) / 60)).padStart(2, "0");
      const s = String(elapsedSec % 60).padStart(2, "0");
      sessionEl.textContent = `${h}:${m}:${s}`;
    }
  }

  tick();
  setInterval(tick, 1000);
}

/**
 * Fetch initial full state from REST endpoints
 */
async function fetchRestSnapshot() {
  try {
    const [healthRes, trackerRes, gunsRes, eventsRes, logsRes, unrealRes, overlayRes, dispRes] = await Promise.all([
      fetch("/api/health/details"),
      fetch("/api/tracker/status"),
      fetch("/api/tracker/guns"),
      fetch("/api/tracker/events"),
      fetch("/api/tracker/logs?limit=50"),
      fetch("/api/tracker/unreal/status"),
      fetch("/api/tracker/overlay/status"),
      fetch("/api/tracker/displays"),
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

    if (unrealRes && unrealRes.ok) {
      const unrealData = await unrealRes.json();
      updateUnrealUI(unrealData);
    }

    if (overlayRes && overlayRes.ok) {
      const overlayData = await overlayRes.json();
      updateOverlayUI(overlayData);
    }

    if (dispRes && dispRes.ok) {
      const dispData = await dispRes.json();
      updateDisplaysUI(dispData);
    }

    // Refresh scenarios and active status snapshot
    loadScenarios();
    fetchActiveScenarioStatus();
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
      // Re-sync REST snapshot and scenario status on reconnect
      fetchRestSnapshot();
      loadScenarios();
      fetchActiveScenarioStatus();
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
      updateScenarioButtonState();
      scheduleReconnect();
    };

    ws.onerror = (err) => {
      console.error("[WS] Error:", err);
      updateScenarioButtonState();
      ws.close();
    };
  } catch (err) {
    updateWsStatus("disconnected", "Offline");
    updateScenarioButtonState();
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
    case "unreal_status":
      updateUnrealUI(data);
      break;
    case "overlay_status":
      updateOverlayUI(data);
      break;
    case "tracker_log":
      appendTrackerLog(data);
      break;
    case "udp_error":
      appendUdpError(data);
      break;
    case "shot_counters_reset":
      resetLocalShotCounters();
      if (data && data.guns) {
        updateGunsTable(data.guns);
      }
      break;
    case "scenario_change_status":
      handleScenarioStatusEvent(data);
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

  const sideApi = document.getElementById("side-api-status");
  if (sideApi) {
    sideApi.textContent = health.status === "ok" ? "Online" : "Warning";
    sideApi.className = health.status === "ok" ? "subsystem-val font-mono text-emerald" : "subsystem-val font-mono text-amber";
  }

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

  const sidePid = document.getElementById("side-tracker-pid");

  if (process) {
    if (procPath) {
      procPath.textContent = process.target_path || "—";
      procPath.title = process.target_path || "";
    }

    if (process.running) {
      if (procHeader) procHeader.textContent = `Running (PID ${process.pid})`;
      if (procDot) procDot.className = "status-dot green";
      if (procBadge) {
        procBadge.className = "badge badge-success";
        procBadge.textContent = "Running";
      }
      if (procState) procState.textContent = `Active (PID ${process.pid})`;
      if (procPid) procPid.textContent = process.pid;

      if (sidePid) {
        sidePid.textContent = `PID ${process.pid}`;
        sidePid.className = "subsystem-val font-mono text-emerald";
      }

      if (btnStart) btnStart.disabled = true;
      if (btnStop) btnStop.disabled = false;
      if (btnRestart) btnRestart.disabled = false;
    } else {
      if (procHeader) procHeader.textContent = "Stopped";
      if (procDot) procDot.className = "status-dot red";
      if (procBadge) {
        procBadge.className = "badge badge-danger";
        procBadge.textContent = "Stopped";
      }
      if (procState) procState.textContent = process.last_error ? "Error" : "Stopped";
      if (procPid) procPid.textContent = "—";

      if (sidePid) {
        sidePid.textContent = "Offline";
        sidePid.className = "subsystem-val font-mono text-muted";
      }

      if (btnStart) btnStart.disabled = false;
      if (btnStop) btnStop.disabled = true;
      if (btnRestart) btnRestart.disabled = false;
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
    if (telemHeader) telemHeader.textContent = "Waiting";
    if (telemDot) telemDot.className = "status-dot gray";
    if (telemBadge) {
      telemBadge.className = "badge badge-gray";
      telemBadge.textContent = "Waiting for gun data";
    }
    return;
  }

  if (telemetry.freshness === "connected") {
    if (telemHeader) telemHeader.textContent = "Connected";
    if (telemDot) telemDot.className = "status-dot green";
    if (telemBadge) {
      telemBadge.className = "badge badge-success";
      telemBadge.textContent = "Connected & Ready";
    }
  } else if (telemetry.freshness === "stale") {
    if (telemHeader) telemHeader.textContent = "Waiting";
    if (telemDot) telemDot.className = "status-dot yellow";
    if (telemBadge) {
      telemBadge.className = "badge badge-warning";
      telemBadge.textContent = `Waiting (${telemetry.seconds_since_last_event}s)`;
    }
  } else {
    if (telemHeader) telemHeader.textContent = "Disconnected";
    if (telemDot) telemDot.className = "status-dot red";
    if (telemBadge) {
      telemBadge.className = "badge badge-danger";
      telemBadge.textContent = "Disconnected";
    }
  }

  if (telemetry.last_valid_event_time) {
    const lastEl = document.getElementById("val-last-event-time");
    if (lastEl) lastEl.textContent = formatTimestamp(telemetry.last_valid_event_time);
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
  // Update guns while strictly preserving active session shot counts
  guns.filter((g) => isPhysicalGun(g)).forEach((g) => {
    const existing = currentGuns.get(g.gun_id) || {};
    const liveShots = sessionShotCounts.get(g.gun_id) || 0;
    currentGuns.set(g.gun_id, {
      ...existing,
      ...g,
      shot_count: liveShots, // Initialized to 0; retains session shots during re-renders
    });
  });
  renderGuns();
}

function renderGuns() {
  const tbody = document.getElementById("guns-table-body");
  if (!tbody) return;

  const sortedGuns = Array.from(currentGuns.values())
    .filter((g) => isPhysicalGun(g))
    .sort((a, b) => a.gun_id - b.gun_id);

  if (sortedGuns.length === 0) {
    tbody.innerHTML = `
      <tr class="empty-row" id="empty-guns-row">
        <td colspan="7">
          <div class="empty-state-tactical">
            <span class="empty-reticle-icon">⌖</span>
            <div class="empty-state-title">No Guns Connected</div>
            <div class="empty-state-desc">Plug in your laser or recoil guns using USB to begin.</div>
          </div>
        </td>
      </tr>
    `;
    updateGunsCounters(0, 0, 0);
    return;
  }

  let html = "";
  let connectedCount = 0;
  let totalShots = 0;

  sortedGuns.forEach((gun) => {
    connectedCount++;
    const gunShots = sessionShotCounts.get(gun.gun_id) || 0;
    gun.shot_count = gunShots;
    totalShots += gunShots;

    const coordsStr = gun.last_shot_coords
      ? `${Math.round(gun.last_shot_coords.x)}, ${Math.round(gun.last_shot_coords.y)}`
      : "—";

    const lastSeenStr = gun.last_seen ? formatTimestamp(gun.last_seen) : "—";

    html += `
      <tr class="gun-row">
        <td>
          <div class="gun-id-cell">
            <span class="gun-badge-pill">G${gun.gun_id}</span>
            <span class="gun-label-text">Gun ${gun.gun_id}</span>
          </div>
        </td>
        <td><span class="lane-tag">Lane ${gun.lane}</span></td>
        <td><span class="port-chip font-mono text-cyan">${gun.port || "USB Auto"}</span></td>
        <td>
          <span class="status-pill-table green">
            <span class="status-dot green"></span>
            <span>Online</span>
          </span>
        </td>
        <td><span class="shots-count-pill font-mono">${gunShots}</span></td>
        <td><span class="coords-display font-mono text-emerald">⌖ ${coordsStr}</span></td>
        <td><span class="time-display font-mono text-muted">${lastSeenStr}</span></td>
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

  if (badge) badge.textContent = `${connected} Connected`;
  if (countText) countText.textContent = `${connected} Connected`;
  if (shotsText) shotsText.textContent = shots;

  const sideGuns = document.getElementById("side-connected-guns");
  const sideShots = document.getElementById("side-total-shots");
  if (sideGuns) sideGuns.textContent = `${connected} / 8`;
  if (sideShots) sideShots.textContent = shots;
}

/**
 * Handle Live Telemetry Events — Trigger Shots
 * Increments the shot counter ONLY when a verified gunshot event is received
 */
function handleLiveShot(data) {
  // Update packet count
  incrementPacketCount();

  const gunId = Number(data.gun);
  const currentCount = sessionShotCounts.get(gunId) || 0;
  const newCount = currentCount + 1;
  sessionShotCounts.set(gunId, newCount);

  // Update gun state with incremented shot count
  const gun = currentGuns.get(gunId) || {
    gun_id: gunId,
    lane: data.lane,
    connected: true,
  };
  gun.connected = true;
  gun.shot_count = newCount;
  gun.last_seen = Date.now() / 1000;
  gun.last_shot_coords = { x: data.x, y: data.y };
  currentGuns.set(gunId, gun);
  renderGuns();

  // Prepend trigger event to live events feed
  appendFeedEvent({
    type: "shot",
    gun: gunId,
    lane: data.lane,
    x: data.x,
    y: data.y,
    round: newCount,
    timestamp: Date.now() / 1000,
  });

  // Update last message & telemetry freshness
  const lastMsg = document.getElementById("val-tracker-last-msg");
  if (lastMsg) lastMsg.textContent = `Shot Fired: Gun ${gunId} (Lane ${data.lane}, Shot #${newCount})`;
  updateTelemetryUI({ freshness: "connected", last_valid_event_time: Date.now() / 1000 });
}

/**
 * Handle Hardware Keepalive / Status
 * Updates connection & port metadata, NEVER modifies or restores shot counters
 */
function handleLiveGunStatus(data) {
  incrementPacketCount();

  const gunId = Number(data.gun);
  if (!data.connected || (data.port && data.port.startsWith("SIM-"))) {
    // If device disconnected or virtual simulation: remove from fleet table
    currentGuns.delete(gunId);
  } else {
    // If real physical hardware connected: update metadata while preserving active session shot count
    const gun = currentGuns.get(gunId) || {
      gun_id: gunId,
      lane: data.lane,
    };
    gun.lane = data.lane;
    gun.port = data.port;
    gun.connected = true;
    gun.shot_count = sessionShotCounts.get(gunId) || 0;
    gun.last_seen = Date.now() / 1000;
    currentGuns.set(gunId, gun);
  }
  renderGuns();

  const statusLabel = data.connected ? "Connected" : "Disconnected";
  const lastMsg = document.getElementById("val-tracker-last-msg");
  if (lastMsg) lastMsg.textContent = `Gun ${gunId} ${statusLabel} (${data.port || "USB"})`;
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
      <div class="feed-item-top">
        <div class="feed-identity">
          <span class="feed-pulse-indicator"></span>
          <span class="feed-gun-tag">G${ev.gun}</span>
          <span class="feed-lane-label">Lane ${ev.lane}</span>
        </div>
        <span class="feed-time-chip font-mono">${timeStr}</span>
      </div>
      <div class="feed-item-stats">
        <div class="feed-stat-box">
          <span class="stat-caption">HIT POINT</span>
          <span class="stat-coord font-mono">X:${Math.round(ev.x)}  Y:${Math.round(ev.y)}</span>
        </div>
        <div class="feed-stat-box round-box">
          <span class="stat-caption">SHOT #</span>
          <span class="stat-round font-mono">#${ev.round}</span>
        </div>
      </div>
    `;
  } else {
    const isConn = ev.connected;
    const badgeClass = isConn ? "status-online" : "status-offline";
    const statusText = isConn ? "Connected" : "Disconnected";
    item.innerHTML = `
      <div class="feed-item-top">
        <div class="feed-identity">
          <span class="feed-dev-tag ${badgeClass}">${statusText}</span>
          <span class="feed-gun-tag">G${ev.gun}</span>
          <span class="feed-lane-label">Lane ${ev.lane}</span>
        </div>
        <span class="feed-time-chip font-mono">${timeStr}</span>
      </div>
      <div class="feed-item-stats">
        <div class="feed-stat-box">
          <span class="stat-caption">PORT</span>
          <span class="stat-coord font-mono">${ev.port || "USB Auto"}</span>
        </div>
        <div class="feed-stat-box round-box">
          <span class="stat-caption">TOTAL SHOTS</span>
          <span class="stat-round font-mono">${ev.shot_count || 0}</span>
        </div>
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
      showToast(`Start failed: ${data.detail?.message || "Unknown error"}`, "error");
    } else {
      showToast("Tracking started", "success");
    }
  } catch (err) {
    showToast(`Start failed: ${err.message}`, "error");
  } finally {
    setButtonLoading(btn, false, "▶ Start Tracking");
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
      showToast(`Stop failed: ${data.detail?.message || "Unknown error"}`, "error");
    } else {
      showToast("Tracking stopped", "info");
    }
  } catch (err) {
    showToast(`Stop failed: ${err.message}`, "error");
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
      showToast(`Restart failed: ${data.detail?.message || "Unknown error"}`, "error");
    } else {
      showToast("Tracking restarted", "success");
    }
  } catch (err) {
    showToast(`Restart failed: ${err.message}`, "error");
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

/**
 * =============================================================================
 * Unreal Engine Simulation Control
 * =============================================================================
 */
function updateUnrealUI(data) {
  if (!data) return;
  const badge = document.getElementById("unreal-status-badge");
  const stateVal = document.getElementById("val-unreal-state");
  const pidVal = document.getElementById("val-unreal-pid");
  const headerVal = document.getElementById("header-unreal-proc");
  const headerDot = document.getElementById("unreal-proc-dot");
  const btnStart = document.getElementById("btn-start-unreal");
  const btnStop = document.getElementById("btn-stop-unreal");

  if (data.is_running) {
    if (badge) {
      badge.className = "badge badge-success";
      badge.textContent = "Running";
    }
    if (stateVal) stateVal.textContent = "Running";
    if (pidVal) pidVal.textContent = data.pid ? String(data.pid) : "Active";
    if (headerVal) headerVal.textContent = "Running";
    if (headerDot) headerDot.className = "status-dot green";
    if (btnStart) btnStart.disabled = true;
    if (btnStop) btnStop.disabled = false;
  } else {
    if (badge) {
      badge.className = "badge badge-danger";
      badge.textContent = "Stopped";
    }
    if (stateVal) stateVal.textContent = "Stopped";
    if (pidVal) pidVal.textContent = "—";
    if (headerVal) headerVal.textContent = "Stopped";
    if (headerDot) headerDot.className = "status-dot red";
    if (btnStart) btnStart.disabled = false;
    if (btnStop) btnStop.disabled = true;
  }
}

async function startUnreal() {
  const btn = document.getElementById("btn-start-unreal");
  setButtonLoading(btn, true, "Starting...");
  try {
    const res = await fetch("/api/tracker/unreal/start", { method: "POST" });
    const data = await res.json();
    if (!res.ok) {
      showToast(`Start failed: ${data.detail || "Unknown error"}`, "error");
    } else {
      showToast("3D simulation started", "success");
    }
    if (data.status) updateUnrealUI(data.status);
  } catch (err) {
    showToast(`Start failed: ${err.message}`, "error");
  } finally {
    setButtonLoading(btn, false, "▶ Start 3D Simulation");
    const uRes = await fetch("/api/tracker/unreal/status");
    if (uRes.ok) updateUnrealUI(await uRes.json());
  }
}

async function stopUnreal() {
  const btn = document.getElementById("btn-stop-unreal");
  setButtonLoading(btn, true, "Stopping...");
  try {
    const res = await fetch("/api/tracker/unreal/stop", { method: "POST" });
    const data = await res.json();
    if (!res.ok) {
      showToast(`Stop failed: ${data.detail || "Unknown error"}`, "error");
    } else {
      showToast("3D simulation stopped", "info");
    }
    if (data.status) updateUnrealUI(data.status);
  } catch (err) {
    showToast(`Stop failed: ${err.message}`, "error");
  } finally {
    setButtonLoading(btn, false, "⏹ Stop");
    const uRes = await fetch("/api/tracker/unreal/status");
    if (uRes.ok) updateUnrealUI(await uRes.json());
  }
}

/**
 * =============================================================================
 * Projector Reticle Overlay Control
 * =============================================================================
 */
function updateOverlayUI(data) {
  if (!data) return;
  const badge = document.getElementById("overlay-status-badge");
  const stateVal = document.getElementById("val-overlay-state");
  const pidVal = document.getElementById("val-overlay-pid");
  const headerVal = document.getElementById("header-overlay-proc");
  const headerDot = document.getElementById("overlay-proc-dot");
  const btnStart = document.getElementById("btn-start-overlay");
  const btnStop = document.getElementById("btn-stop-overlay");

  const hudStatus = document.getElementById("hud-bot-status");
  const hudBorder = document.querySelector(".hud-screen-border");

  if (data.is_running) {
    if (badge) {
      badge.className = "badge badge-success";
      badge.textContent = "Active";
    }
    if (stateVal) stateVal.textContent = "Active";
    if (pidVal) pidVal.textContent = data.pid ? String(data.pid) : "Active";
    if (headerVal) headerVal.textContent = "Active";
    if (headerDot) headerDot.className = "status-dot green";

    const targetVal = document.getElementById("val-overlay-target-display");
    if (targetVal && data.active_identity) {
      targetVal.textContent = data.active_identity;
    }

    if (hudStatus) {
      hudStatus.textContent = "Screen Active";
      hudStatus.className = "hud-bot-status text-emerald";
    }
    if (hudBorder) {
      hudBorder.style.borderColor = "var(--accent-emerald)";
      hudBorder.style.boxShadow = "0 0 14px rgba(16, 185, 129, 0.4)";
    }
    if (btnStart) btnStart.disabled = true;
    if (btnStop) btnStop.disabled = false;
  } else {
    if (badge) {
      badge.className = "badge badge-gray";
      badge.textContent = "Inactive";
    }
    if (stateVal) stateVal.textContent = "Inactive";
    if (pidVal) pidVal.textContent = "—";
    if (headerVal) headerVal.textContent = "Off";
    if (headerDot) headerDot.className = "status-dot gray";
    if (hudStatus) {
      hudStatus.textContent = "Screen Standby";
      hudStatus.className = "hud-bot-status text-muted";
    }
    if (hudBorder) {
      hudBorder.style.borderColor = "var(--border-strong)";
      hudBorder.style.boxShadow = "none";
    }
    if (btnStart) btnStart.disabled = false;
    if (btnStop) btnStop.disabled = true;
  }
}

async function startOverlay() {
  const btn = document.getElementById("btn-start-overlay");
  setButtonLoading(btn, true, "Starting...");
  try {
    const res = await fetch("/api/tracker/overlay/start", { method: "POST" });
    const data = await res.json();
    if (!res.ok) {
      showToast(`Start failed: ${data.detail || "Unknown error"}`, "error");
    } else {
      showToast("Target screen started", "success");
    }
    if (data.status) updateOverlayUI(data.status);
  } catch (err) {
    showToast(`Start failed: ${err.message}`, "error");
  } finally {
    setButtonLoading(btn, false, "▶ Start Target Screen");
    const oRes = await fetch("/api/tracker/overlay/status");
    if (oRes.ok) updateOverlayUI(await oRes.json());
  }
}

async function stopOverlay() {
  const btn = document.getElementById("btn-stop-overlay");
  setButtonLoading(btn, true, "Stopping...");
  try {
    const res = await fetch("/api/tracker/overlay/stop", { method: "POST" });
    const data = await res.json();
    if (!res.ok) {
      showToast(`Stop failed: ${data.detail || "Unknown error"}`, "error");
    } else {
      showToast("Target screen closed", "info");
    }
    if (data.status) updateOverlayUI(data.status);
  } catch (err) {
    showToast(`Stop failed: ${err.message}`, "error");
  } finally {
    setButtonLoading(btn, false, "⏹ Stop");
    const oRes = await fetch("/api/tracker/overlay/status");
    if (oRes.ok) updateOverlayUI(await oRes.json());
  }
}

/**
 * =============================================================================
 * Hardware Display & Projector Detection
 * =============================================================================
 */
function updateDisplaysUI(displays) {
  if (!displays || !displays.length) return;
  const countBadge = document.getElementById("displays-count-badge");
  const primaryVal = document.getElementById("val-display-primary");
  const secondaryVal = document.getElementById("val-display-secondary");
  const unrealTarget = document.getElementById("val-unreal-target-display");
  const overlayTarget = document.getElementById("val-overlay-target-display");

  if (countBadge) countBadge.textContent = `${displays.length} Connected`;

  const primary = displays.find((d) => d.is_primary) || displays[0];
  const secondary = displays.find((d) => !d.is_primary);
  const target = secondary || primary;

  if (target) {
    const hudRes = document.getElementById("hud-bar-res");
    const hudTR = document.getElementById("hud-tag-tr");
    const hudBL = document.getElementById("hud-tag-bl");
    const hudBR = document.getElementById("hud-tag-br");
    if (hudRes) hudRes.textContent = `${target.width}×${target.height} • 60 FPS`;
    if (hudTR) hudTR.textContent = `(${target.width},0)`;
    if (hudBL) hudBL.textContent = `(0,${target.height})`;
    if (hudBR) hudBR.textContent = `(${target.width},${target.height})`;
  }

  if (primary && primaryVal) {
    primaryVal.textContent = `${primary.width}×${primary.height} (${primary.x},${primary.y})`;
  }
  if (secondary) {
    if (secondaryVal) secondaryVal.textContent = `Display ${secondary.index} (${secondary.width}×${secondary.height})`;
    if (unrealTarget) unrealTarget.textContent = `Display ${secondary.index} (${secondary.width}×${secondary.height})`;
    if (overlayTarget) overlayTarget.textContent = `Display ${secondary.index} (${secondary.width}×${secondary.height})`;
  } else {
    if (secondaryVal) secondaryVal.textContent = "None (Using Primary)";
    if (unrealTarget) unrealTarget.textContent = `Display ${primary.index} (${primary.width}×${primary.height})`;
    if (overlayTarget) overlayTarget.textContent = `Display ${primary.index} (${primary.width}×${primary.height})`;
  }
}

/**
 * =============================================================================
 * Fullscreen & Window Operations
 * =============================================================================
 */
function toggleFullscreen() {
  if (!document.fullscreenElement) {
    if (document.documentElement.requestFullscreen) {
      document.documentElement.requestFullscreen().catch(() => {});
    }
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen().catch(() => {});
    }
  }
}

function exitApplication() {
  showTacticalModal({
    title: "Exit Console?",
    message: "Are you sure you want to exit the console?",
    type: "danger",
    confirmText: "Exit",
    cancelText: "Stay",
    showCancel: true,
    onConfirm: async () => {
      // Trigger shutdown splash screen
      const shutdownSplash = document.getElementById("shutdown-splash-screen");
      const shutdownBar = document.getElementById("shutdown-progress-bar");
      const shutdownLog = document.getElementById("shutdown-log-text");

      if (shutdownSplash) {
        shutdownSplash.classList.add("active");
        if (shutdownBar) shutdownBar.style.width = "40%";
        if (shutdownLog) shutdownLog.textContent = "CLOSING SIMULATOR & SCREENS...";
      }

      try {
        if (shutdownBar) shutdownBar.style.width = "75%";
        await fetch("/api/tracker/app/exit", { method: "POST" });
        if (shutdownBar) shutdownBar.style.width = "100%";
        if (shutdownLog) shutdownLog.textContent = "APPLICATION CLOSED.";
      } catch (e) {
        try {
          await fetch("/api/tracker/all/stop", { method: "POST" });
        } catch (_) {}
      }

      setTimeout(() => {
        try {
          window.close();
        } catch (_) {}
      }, 500);
    },
  });
}

/**
 * =============================================================================
 * Tactical Modal Dialog Engine (Dark Glassmorphic Aesthetic)
 * =============================================================================
 */
let modalResolve = null;

function showTacticalModal({
  title = "Notice",
  message = "",
  type = "info", // "info", "warning", "danger", "success"
  confirmText = "Confirm",
  cancelText = "Cancel",
  showCancel = true,
  onConfirm = null,
  onCancel = null,
}) {
  const backdrop = document.getElementById("tactical-modal");
  const titleEl = document.getElementById("modal-title");
  const messageEl = document.getElementById("modal-message");
  const badgeEl = document.getElementById("modal-icon-badge");
  const confirmBtn = document.getElementById("modal-btn-confirm");
  const cancelBtn = document.getElementById("modal-btn-cancel");

  if (!backdrop) return;

  if (titleEl) titleEl.textContent = title;
  if (messageEl) messageEl.textContent = message;

  // Set badge icon and color if badge element exists
  if (badgeEl) {
    badgeEl.className = `modal-icon-badge ${type}`;
    if (type === "danger") badgeEl.textContent = "✕";
    else if (type === "warning") badgeEl.textContent = "⚠";
    else if (type === "success") badgeEl.textContent = "✓";
    else badgeEl.textContent = "⌖";
  }

  if (confirmBtn) {
    confirmBtn.className = type === "danger" ? "btn btn-danger" : "btn btn-primary";
    confirmBtn.textContent = confirmText;
  }
  if (cancelBtn) {
    if (showCancel) {
      cancelBtn.style.display = "inline-flex";
      cancelBtn.textContent = cancelText;
    } else {
      cancelBtn.style.display = "none";
    }
  }

  backdrop.classList.add("active");
  backdrop.setAttribute("aria-hidden", "false");

  return new Promise((resolve) => {
    if (confirmBtn) {
      confirmBtn.onclick = () => {
        closeTacticalModal();
        if (typeof onConfirm === "function") onConfirm();
        resolve(true);
      };
    }

    if (cancelBtn) {
      cancelBtn.onclick = () => {
        closeTacticalModal();
        if (typeof onCancel === "function") onCancel();
        resolve(false);
      };
    }

    modalResolve = resolve;
  });
}

function closeTacticalModal() {
  const backdrop = document.getElementById("tactical-modal");
  if (backdrop) {
    if (document.activeElement && backdrop.contains(document.activeElement)) {
      document.activeElement.blur();
    }
    backdrop.classList.remove("active");
    backdrop.setAttribute("aria-hidden", "true");
  }
  if (modalResolve) {
    modalResolve(false);
    modalResolve = null;
  }
}

// Global modal keyboard handling (Escape to close, Enter to confirm)
document.addEventListener("keydown", (e) => {
  const backdrop = document.getElementById("tactical-modal");
  if (backdrop && backdrop.classList.contains("active")) {
    if (e.key === "Escape") {
      e.preventDefault();
      closeTacticalModal();
    } else if (e.key === "Enter") {
      e.preventDefault();
      const confirmBtn = document.getElementById("modal-btn-confirm");
      if (confirmBtn) confirmBtn.click();
    }
  }
});

/**
 * =============================================================================
 * Tactical Toast Notification System
 * =============================================================================
 */
function showToast(message, type = "info", duration = 4000) {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;

  const icon = document.createElement("span");
  icon.className = "toast-icon";
  if (type === "success") icon.textContent = "✓";
  else if (type === "error") icon.textContent = "✕";
  else if (type === "warning") icon.textContent = "⚠";
  else icon.textContent = "ℹ";

  const msg = document.createElement("span");
  msg.className = "toast-message";
  msg.textContent = message;

  toast.appendChild(icon);
  toast.appendChild(msg);
  container.appendChild(toast);

  // Trigger CSS transition
  requestAnimationFrame(() => {
    toast.classList.add("show");
  });

  const timer = setTimeout(() => {
    dismiss();
  }, duration);

  function dismiss() {
    clearTimeout(timer);
    toast.classList.remove("show");
    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 300);
  }

  toast.onclick = dismiss;
}

// Global browser alert override to route into tactical toast
window.alert = function (msg) {
  showToast(String(msg), "warning", 5000);
};

/**
 * =============================================================================
 * Scenario Selection & Unreal Engine Level Transition Management
 * =============================================================================
 */

async function loadScenarios() {
  const selectEl = document.getElementById("scenario-select-dropdown");
  const descEl = document.getElementById("scenario-desc-text");
  if (!selectEl) return;

  try {
    const res = await fetch("/api/scenarios");
    if (!res.ok) {
      console.warn("[Scenario] Failed to fetch scenarios list:", res.status);
      return;
    }
    const scenarios = await res.json();
    if (!Array.isArray(scenarios)) return;

    availableScenarios = scenarios;

    // Preserve previously selected scenario if still in list
    const previousSelection = selectEl.value;

    selectEl.innerHTML = "";

    if (scenarios.length === 0) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "No scenarios configured";
      opt.disabled = true;
      opt.selected = true;
      selectEl.appendChild(opt);
      if (descEl) descEl.textContent = "No scenarios available on backend.";
      updateScenarioButtonState();
      return;
    }

    scenarios.filter((sc) => sc.available).forEach((sc) => {
      const opt = document.createElement("option");
      opt.value = sc.scenario_id;
      opt.textContent = sc.display_name;
      selectEl.appendChild(opt);
    });

    // Restore or pick first available
    let matchedOpt = null;
    if (previousSelection) {
      matchedOpt = scenarios.find((s) => s.scenario_id === previousSelection && s.available);
    }
    if (!matchedOpt) {
      matchedOpt = scenarios.find((s) => s.available) || scenarios[0];
    }

    if (matchedOpt) {
      selectEl.value = matchedOpt.scenario_id;
      selectedScenarioId = matchedOpt.scenario_id;
      if (descEl) descEl.textContent = matchedOpt.description || "No description provided.";
    }

    updateScenarioButtonState();
  } catch (err) {
    console.error("[Scenario] Error loading scenarios:", err);
  }
}

function onScenarioSelectChange() {
  const selectEl = document.getElementById("scenario-select-dropdown");
  const descEl = document.getElementById("scenario-desc-text");
  if (!selectEl) return;

  selectedScenarioId = selectEl.value;
  const matched = availableScenarios.find((s) => s.scenario_id === selectedScenarioId);
  if (matched && descEl) {
    descEl.textContent = matched.description || "No description provided.";
  }
  updateScenarioButtonState();
}

async function fetchActiveScenarioStatus() {
  try {
    const res = await fetch("/api/scenarios/active");
    if (res.ok) {
      const data = await res.json();
      handleScenarioStatusEvent(data);
    }
  } catch (err) {
    // Normal before any scenario command has been dispatched
    console.debug("[Scenario] No active scenario command snapshot:", err);
  }
}

function updateCurrentScenarioDisplay(displayName) {
  currentScenarioName = displayName;
  const currentEl = document.getElementById("current-scenario-name");
  const sideEl = document.getElementById("side-scenario-name");
  if (currentEl) currentEl.textContent = displayName;
  if (sideEl) sideEl.textContent = displayName;
}

function setScenarioStatusUI(state, label, detail) {
  // Status displays removed per user requirement
}

function updateScenarioButtonState() {
  const btn = document.getElementById("btn-change-scenario");
  const selectEl = document.getElementById("scenario-select-dropdown");
  if (!btn) return;

  const hasSelection = selectEl && selectEl.value && selectEl.value.length > 0;
  btn.disabled = !hasSelection;
}

function showScenarioError(msg) {
  const banner = document.getElementById("scenario-error-banner");
  const textEl = document.getElementById("scenario-error-text");
  if (banner && textEl) {
    textEl.textContent = msg;
    banner.style.display = "flex";
  }
}

function dismissScenarioError() {
  const banner = document.getElementById("scenario-error-banner");
  if (banner) {
    banner.style.display = "none";
  }
}

async function requestScenarioChange() {
  const selectEl = document.getElementById("scenario-select-dropdown");
  const scenarioId = selectEl ? selectEl.value : selectedScenarioId;

  if (!scenarioId) {
    showToast("Please select a scenario first", "warning");
    return;
  }

  const selectedObj = availableScenarios.find((s) => s.scenario_id === scenarioId);
  const targetName = selectedObj ? selectedObj.display_name : scenarioId;

  // Immediately update current scenario display without waiting or checking
  updateCurrentScenarioDisplay(targetName);
  showToast(`Scenario changed to ${targetName}`, "success");

  // Send change command to backend directly (fire-and-forget)
  try {
    fetch("/api/scenarios/change", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario_id: scenarioId }),
    }).catch((err) => console.warn("[Scenario] Request error:", err));
  } catch (err) {
    console.warn("[Scenario] Request error:", err);
  }
}

function handleScenarioStatusEvent(data) {
  // Fire-and-forget: do not track or check whether changed or not
  if (!data) return;
  console.debug("[Scenario] Status event:", data);
}


