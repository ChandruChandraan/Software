import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  Gun,
  ShotEvent,
  Scenario,
  ProcessStatus,
  TelemetryStatus,
  UnrealStatus,
  OverlayStatus,
  DisplayInfo,
  LogEntry,
  UdpErrorEntry,
  HealthDetails,
} from "@/types/simulator";
import { Sidebar } from "@/components/Sidebar";
import { SplashScreen } from "@/components/SplashScreen";
import { ShutdownScreen } from "@/components/ShutdownScreen";
import { ScenarioSelector } from "@/components/ScenarioSelector";
import { GunsTable } from "@/components/GunsTable";
import { LiveShotFeed } from "@/components/LiveShotFeed";
import { SubsystemManager } from "@/components/SubsystemManager";
import { DiagnosticsPanel } from "@/components/DiagnosticsPanel";
import {
  Dialog,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Maximize2, Radio, AlertTriangle } from "lucide-react";
import { formatTime } from "@/lib/utils";

export const App: React.FC = () => {
  // Splash & Shutdown Screen States
  const [splashActive, setSplashActive] = useState<boolean>(true);
  const [shutdownState, setShutdownState] = useState<{
    active: boolean;
    progress: number;
    message: string;
  }>({
    active: false,
    progress: 0,
    message: "",
  });
  const [exitModalOpen, setExitModalOpen] = useState<boolean>(false);
  const handleDismissSplash = useCallback(() => setSplashActive(false), []);

  // Active View Tab
  const [activeTab, setActiveTab] = useState<string>("overview");

  // Core Simulation States
  const [guns, setGuns] = useState<Map<number, Gun>>(new Map());
  const [sessionShotCounts, setSessionShotCounts] = useState<Map<number, number>>(new Map());
  const [events, setEvents] = useState<ShotEvent[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [udpErrors, setUdpErrors] = useState<UdpErrorEntry[]>([]);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [currentScenario, setCurrentScenario] = useState<string>("Indoor Shooting Range");
  const [health, setHealth] = useState<HealthDetails | null>(null);
  const [trackerProcess, setTrackerProcess] = useState<ProcessStatus | null>(null);
  const [telemetry, setTelemetry] = useState<TelemetryStatus | null>(null);
  const [unrealStatus, setUnrealStatus] = useState<UnrealStatus | null>(null);
  const [overlayStatus, setOverlayStatus] = useState<OverlayStatus | null>(null);
  const [displays, setDisplays] = useState<DisplayInfo[]>([]);

  // Telemetry indicators
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [backendUptime, setBackendUptime] = useState<number>(0);
  const [isResettingShots, setIsResettingShots] = useState<boolean>(false);

  // Session shots ref for stable reference
  const sessionShotCountsRef = useRef<Map<number, number>>(new Map());

  // WebSocket Ref
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Uptime Ticker
  useEffect(() => {
    const timer = setInterval(() => {
      setBackendUptime((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Keyboard shortcut F11 for Fullscreen
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "F11") {
        e.preventDefault();
        if (!document.fullscreenElement) {
          document.documentElement.requestFullscreen().catch(() => {});
        } else {
          document.exitFullscreen().catch(() => {});
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // 1. Fetch REST Snapshot
  const fetchRestSnapshot = useCallback(async () => {
    try {
      const [
        healthRes,
        trackerRes,
        gunsRes,
        eventsRes,
        logsRes,
        unrealRes,
        overlayRes,
        dispRes,
        scenariosRes,
      ] = await Promise.all([
        fetch("/api/health/details").catch(() => null),
        fetch("/api/tracker/status").catch(() => null),
        fetch("/api/tracker/guns").catch(() => null),
        fetch("/api/tracker/events").catch(() => null),
        fetch("/api/tracker/logs?limit=50").catch(() => null),
        fetch("/api/tracker/unreal/status").catch(() => null),
        fetch("/api/tracker/overlay/status").catch(() => null),
        fetch("/api/tracker/displays").catch(() => null),
        fetch("/api/scenarios").catch(() => null),
      ]);

      if (healthRes && healthRes.ok) {
        const data = await healthRes.json();
        setHealth(data);
        if (data.uptime_seconds) {
          setBackendUptime(Math.floor(data.uptime_seconds));
        }
      }

      if (trackerRes && trackerRes.ok) {
        const data = await trackerRes.json();
        setTrackerProcess(data.process);
        setTelemetry(data.telemetry);
      }

      if (gunsRes && gunsRes.ok) {
        const data: Gun[] = await gunsRes.json();
        setGuns((prev) => {
          const next = new Map(prev);
          data.forEach((g) => {
            const existing = next.get(g.gun_id) || {};
            const liveShots = sessionShotCountsRef.current.get(g.gun_id) || 0;
            next.set(g.gun_id, {
              ...existing,
              ...g,
              shot_count: liveShots,
            });
          });
          return next;
        });
      }

      if (eventsRes && eventsRes.ok) {
        const data: ShotEvent[] = await eventsRes.json();
        setEvents(data.filter((e) => e.type === "shot").slice(0, 50));
      }

      if (logsRes && logsRes.ok) {
        const data: LogEntry[] = await logsRes.json();
        setLogs(data);
      }

      if (unrealRes && unrealRes.ok) {
        setUnrealStatus(await unrealRes.json());
      }

      if (overlayRes && overlayRes.ok) {
        setOverlayStatus(await overlayRes.json());
      }

      if (dispRes && dispRes.ok) {
        setDisplays(await dispRes.json());
      }

      if (scenariosRes && scenariosRes.ok) {
        const scData: Scenario[] = await scenariosRes.json();
        setScenarios(scData);
      }

      // Snapshot active scenario
      const activeRes = await fetch("/api/scenarios/active").catch(() => null);
      if (activeRes && activeRes.ok) {
        const activeData = await activeRes.json();
        if (activeData.display_name) {
          setCurrentScenario(activeData.display_name);
        }
      }
    } catch (err) {
      console.warn("[REST Snapshot] Error fetching simulator state:", err);
    }
  }, []);

  // 2. Setup WebSocket Connection
  const connectWebSocket = useCallback(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/backend`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setWsConnected(true);
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
        fetchRestSnapshot();
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          const topic = payload.topic;
          const data = payload.data;

          switch (topic) {
            case "shot": {
              const gunId = Number(data.gun);
              const nextShots = (sessionShotCountsRef.current.get(gunId) || 0) + 1;
              sessionShotCountsRef.current.set(gunId, nextShots);

              setSessionShotCounts((prev) => {
                const nextMap = new Map(prev);
                nextMap.set(gunId, nextShots);
                return nextMap;
              });

              setGuns((prev) => {
                const nextMap = new Map(prev);
                const existing = nextMap.get(gunId) || {
                  gun_id: gunId,
                  lane: data.lane,
                  connected: true,
                  shot_count: 0,
                };
                nextMap.set(gunId, {
                  ...existing,
                  connected: true,
                  shot_count: nextShots,
                  last_seen: Date.now() / 1000,
                  last_shot_coords: { x: data.x, y: data.y },
                });
                return nextMap;
              });

              setEvents((prev) => [
                {
                  id: `${Date.now()}-${Math.random()}`,
                  type: "shot",
                  gun: gunId,
                  lane: data.lane,
                  x: data.x,
                  y: data.y,
                  round: nextShots,
                  timestamp: Date.now() / 1000,
                },
                ...prev.slice(0, 49),
              ]);
              break;
            }

            case "gun_status": {
              const gunId = Number(data.gun);
              if (!data.connected || (data.port && data.port.startsWith("SIM-"))) {
                setGuns((prev) => {
                  const nextMap = new Map(prev);
                  nextMap.delete(gunId);
                  return nextMap;
                });
              } else {
                setGuns((prev) => {
                  const nextMap = new Map(prev);
                  const existing = nextMap.get(gunId) || {
                    gun_id: gunId,
                    lane: data.lane,
                    connected: true,
                    shot_count: 0,
                  };
                  nextMap.set(gunId, {
                    ...existing,
                    lane: data.lane,
                    port: data.port,
                    connected: true,
                    shot_count: sessionShotCounts.get(gunId) || 0,
                    last_seen: Date.now() / 1000,
                  });
                  return nextMap;
                });
              }
              break;
            }

            case "tracker_started":
            case "tracker_stopped":
            case "tracker_crashed":
              fetchRestSnapshot();
              break;

            case "unreal_status":
              setUnrealStatus(data);
              break;

            case "overlay_status":
              setOverlayStatus(data);
              break;

            case "tracker_log":
              setLogs((prev) => [...prev, data].slice(-200));
              break;

            case "udp_error":
              setUdpErrors((prev) => [
                ...prev,
                {
                  error: data.error,
                  raw: data.raw,
                  timestamp: Date.now() / 1000,
                },
              ].slice(-100));
              break;

            case "shot_counters_reset":
              sessionShotCountsRef.current.clear();
              setSessionShotCounts(new Map());
              setGuns((prev) => {
                const nextMap = new Map();
                prev.forEach((gun, id) => {
                  nextMap.set(id, {
                    ...gun,
                    shot_count: 0,
                    last_shot_coords: null,
                  });
                });
                return nextMap;
              });
              setEvents([]);
              break;

            case "scenario_change_status":
              if (data && data.display_name) {
                setCurrentScenario(data.display_name);
              }
              break;

            default:
              break;
          }
        } catch (err) {
          console.warn("[WS Parse error]", err);
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
        scheduleReconnect();
      };

      ws.onerror = () => {
        setWsConnected(false);
        ws.close();
      };
    } catch {
      setWsConnected(false);
      scheduleReconnect();
    }
  }, [fetchRestSnapshot]);

  const scheduleReconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) return;
    reconnectTimeoutRef.current = setTimeout(() => {
      reconnectTimeoutRef.current = null;
      connectWebSocket();
    }, 2000);
  }, [connectWebSocket]);

  // Initial Boot
  useEffect(() => {
    fetchRestSnapshot();
    connectWebSocket();
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    };
  }, [connectWebSocket, fetchRestSnapshot]);

  // Actions
  const handleResetShots = async () => {
    setIsResettingShots(true);
    try {
      await fetch("/api/tracker/reset-shots", { method: "POST" });
      sessionShotCountsRef.current.clear();
      setSessionShotCounts(new Map());
      setGuns((prev) => {
        const nextMap = new Map();
        prev.forEach((gun, id) => {
          nextMap.set(id, {
            ...gun,
            shot_count: 0,
            last_shot_coords: null,
          });
        });
        return nextMap;
      });
      setEvents([]);
    } catch (err) {
      console.warn("Failed to reset shots:", err);
    } finally {
      setIsResettingShots(false);
    }
  };

  const handleClearFeed = async () => {
    try {
      await fetch("/api/tracker/clear-events", { method: "POST" });
      setEvents([]);
    } catch (err) {
      console.warn("Failed to clear feed:", err);
    }
  };

  const handleScenarioChange = async (scenarioId: string) => {
    const sc = scenarios.find((s) => s.scenario_id === scenarioId);
    if (sc) {
      setCurrentScenario(sc.display_name);
    }
    const res = await fetch("/api/scenarios/change", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario_id: scenarioId }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || "Scenario change command rejected by backend");
    }
  };

  // Subsystem control triggers
  const handleStartTracker = async () => {
    await fetch("/api/tracker/start", { method: "POST" });
    fetchRestSnapshot();
  };

  const handleStopTracker = async () => {
    await fetch("/api/tracker/stop", { method: "POST" });
    fetchRestSnapshot();
  };

  const handleRestartTracker = async () => {
    await fetch("/api/tracker/restart", { method: "POST" });
    fetchRestSnapshot();
  };

  const handleStartUnreal = async () => {
    await fetch("/api/tracker/unreal/start", { method: "POST" });
    fetchRestSnapshot();
  };

  const handleStopUnreal = async () => {
    await fetch("/api/tracker/unreal/stop", { method: "POST" });
    fetchRestSnapshot();
  };

  const handleStartOverlay = async () => {
    await fetch("/api/tracker/overlay/start", { method: "POST" });
    fetchRestSnapshot();
  };

  const handleStopOverlay = async () => {
    await fetch("/api/tracker/overlay/stop", { method: "POST" });
    fetchRestSnapshot();
  };

  // Exit sequence
  const confirmExitApplication = async () => {
    setExitModalOpen(false);
    setShutdownState({
      active: true,
      progress: 30,
      message: "CLOSING 3D SIMULATOR & SCREENS...",
    });

    try {
      setShutdownState((prev) => ({ ...prev, progress: 65 }));
      await fetch("/api/tracker/app/exit", { method: "POST" });
      setShutdownState((prev) => ({ ...prev, progress: 100, message: "APPLICATION TERMINATED." }));
    } catch {
      try {
        await fetch("/api/tracker/all/stop", { method: "POST" });
      } catch {}
    }

    setTimeout(() => {
      try {
        window.close();
      } catch {}
    }, 600);
  };

  // Metrics
  const connectedGuns = Array.from(guns.values()).filter(
    (g) => g.connected && g.port && !g.port.startsWith("SIM-")
  );
  const totalShotsCount = connectedGuns.reduce((acc, g) => acc + g.shot_count, 0);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-black text-white font-sans tactical-grid-bg">
      {/* Launch Splash Screen */}
      {splashActive && <SplashScreen onComplete={handleDismissSplash} />}

      {/* Shutdown Splash Screen */}
      {shutdownState.active && (
        <ShutdownScreen
          progress={shutdownState.progress}
          message={shutdownState.message}
        />
      )}

      {/* Main Tactical Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onExitClick={() => setExitModalOpen(true)}
        serverOnline={health?.status === "ok"}
        wsConnected={wsConnected}
        trackerPid={trackerProcess?.pid}
        trackerRunning={!!trackerProcess?.running}
        currentScenario={currentScenario}
        connectedGunsCount={connectedGuns.length}
        totalShotsCount={totalShotsCount}
      />

      {/* Main Operations Stage */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Top Cockpit Telemetry Bar */}
        <header className="h-14 border-b border-zinc-800 bg-zinc-950/80 px-6 flex items-center justify-between shrink-0 select-none">
          {/* Left indicators */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 font-mono text-xs">
              <span className="text-zinc-500 uppercase text-[10px]">Uptime:</span>
              <span className="text-white font-bold">{formatTime(backendUptime)}</span>
            </div>

            <div className="h-4 w-px bg-zinc-800" />

            <div className="flex items-center space-x-2 font-mono text-xs">
              <Radio className={`w-3.5 h-3.5 ${wsConnected ? "text-white" : "text-zinc-600"}`} />
              <span className="text-zinc-400">WebSocket:</span>
              <span className="text-white font-bold">{wsConnected ? "127.0.0.1:8080" : "Offline"}</span>
            </div>

            <div className="h-4 w-px bg-zinc-800" />

            <div className="flex items-center space-x-2 font-mono text-xs">
              <span className="text-zinc-500 uppercase text-[10px]">Active Deck:</span>
              <Badge variant="outline" className="text-[10px] font-mono border-zinc-700 bg-zinc-900 text-white font-bold uppercase">
                {activeTab}
              </Badge>
            </div>
          </div>

          {/* Right Action buttons */}
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="xs"
              onClick={() => {
                if (!document.fullscreenElement) {
                  document.documentElement.requestFullscreen().catch(() => {});
                } else {
                  document.exitFullscreen().catch(() => {});
                }
              }}
              className="font-mono text-xs border-zinc-700 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white"
              title="Toggle Fullscreen (F11)"
            >
              <Maximize2 className="w-3.5 h-3.5 mr-1" />
              Fullscreen [F11]
            </Button>
          </div>
        </header>

        {/* Scrollable Main Content Viewport */}
        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          {activeTab === "overview" && (
            <>
              {/* Section 01: Scenario Selection */}
              <ScenarioSelector
                scenarios={scenarios}
                currentScenario={currentScenario}
                onScenarioChange={handleScenarioChange}
              />

              {/* Panoramic Operations Row (Connected Guns Fleet + Live Telemetry Feed) */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                {/* Left 8 cols: Guns Table */}
                <div className="lg:col-span-8">
                  <GunsTable
                    guns={Array.from(guns.values())}
                    onResetShots={handleResetShots}
                    isResetting={isResettingShots}
                  />
                </div>

                {/* Right 4 cols: Live Feed */}
                <div className="lg:col-span-4">
                  <LiveShotFeed
                    events={events}
                    onClearFeed={handleClearFeed}
                  />
                </div>
              </div>
            </>
          )}

          {activeTab === "hardware" && (
            <SubsystemManager
              trackerProcess={trackerProcess}
              telemetry={telemetry}
              unrealStatus={unrealStatus}
              overlayStatus={overlayStatus}
              displays={displays}
              onStartTracker={handleStartTracker}
              onStopTracker={handleStopTracker}
              onRestartTracker={handleRestartTracker}
              onStartUnreal={handleStartUnreal}
              onStopUnreal={handleStopUnreal}
              onStartOverlay={handleStartOverlay}
              onStopOverlay={handleStopOverlay}
            />
          )}

          {activeTab === "diagnostics" && (
            <DiagnosticsPanel
              logs={logs}
              udpErrors={udpErrors}
              onClearLogs={() => setLogs([])}
            />
          )}
        </main>

        {/* Tactical Footer */}
        <footer className="h-9 border-t border-zinc-800 bg-black px-6 flex items-center justify-between text-xs font-mono text-zinc-500 shrink-0 select-none">
          <div className="flex items-center space-x-3">
            <span>FiringSim Tactical Operations Console</span>
            <span>•</span>
            <span>Dual Display Framework</span>
            <span>•</span>
            <span>Laser & Recoil Tracking</span>
          </div>
          <div>
            <span>Full Black & White Noir Edition</span>
          </div>
        </footer>
      </div>

      {/* Exit Confirmation Dialog */}
      <Dialog open={exitModalOpen} onOpenChange={setExitModalOpen}>
        <DialogHeader>
          <div className="w-10 h-10 rounded-full border border-zinc-700 bg-zinc-900 flex items-center justify-center mb-2 mx-auto sm:mx-0">
            <AlertTriangle className="w-5 h-5 text-white" />
          </div>
          <DialogTitle className="text-base font-mono uppercase tracking-wider">
            Exit Console Application?
          </DialogTitle>
          <DialogDescription className="text-zinc-400 font-mono text-xs">
            Exiting will safely terminate all running background services, including Unreal Engine 3D Simulation and Projector Target Screen.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="mt-6 flex space-x-2">
          <Button
            variant="outline"
            onClick={() => setExitModalOpen(false)}
            className="font-mono text-xs border-zinc-700 bg-zinc-900 text-zinc-300 hover:text-white"
          >
            Stay
          </Button>
          <Button
            variant="default"
            onClick={confirmExitApplication}
            className="font-mono text-xs font-bold"
          >
            Exit Application
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
};
