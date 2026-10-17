import React, { useEffect, useState } from "react";
import { Crosshair, LogOut, LayoutDashboard, Cpu, Terminal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn, formatTime } from "@/lib/utils";

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  onExitClick: () => void;
  serverOnline: boolean;
  wsConnected: boolean;
  trackerPid: number | null | undefined;
  trackerRunning: boolean;
  currentScenario: string;
  connectedGunsCount: number;
  totalShotsCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  onExitClick,
  serverOnline,
  wsConnected,
  trackerPid,
  trackerRunning,
  currentScenario,
  connectedGunsCount,
  totalShotsCount,
}) => {
  const [localTime, setLocalTime] = useState("");
  const [sessionSeconds, setSessionSeconds] = useState(0);

  useEffect(() => {
    const tick = () => {
      const now = new Date();
      setLocalTime(now.toTimeString().split(" ")[0]);
      setSessionSeconds((prev) => prev + 1);
    };
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <aside className="w-72 bg-black border-r border-zinc-800 flex flex-col justify-between h-screen shrink-0 select-none">
      {/* Brand Header */}
      <div>
        <div className="p-5 border-b border-zinc-800/80 flex items-center space-x-3">
          <div className="w-9 h-9 rounded-md bg-zinc-900 border border-zinc-700 flex items-center justify-center shrink-0">
            <Crosshair className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-wider uppercase text-white font-mono">
              FIRINGSIM
            </h1>
            <p className="text-[10px] uppercase font-mono tracking-widest text-zinc-400">
              Control Center v2.0
            </p>
          </div>
        </div>

        {/* Real-time Cockpit Clock */}
        <div className="p-4 border-b border-zinc-800/80 bg-zinc-950/60">
          <div className="grid grid-cols-2 gap-2 text-center">
            <div className="p-2 rounded bg-zinc-900/60 border border-zinc-800">
              <span className="text-[10px] font-mono text-zinc-400 uppercase tracking-wider block">
                Local Time
              </span>
              <span className="text-xs font-mono font-bold text-white">
                {localTime || "12:00:00"}
              </span>
            </div>
            <div className="p-2 rounded bg-zinc-900/60 border border-zinc-800">
              <span className="text-[10px] font-mono text-zinc-400 uppercase tracking-wider block">
                Session
              </span>
              <span className="text-xs font-mono font-bold text-white">
                {formatTime(sessionSeconds)}
              </span>
            </div>
          </div>
        </div>

        {/* Navigation Items */}
        <div className="p-3 space-y-1">
          <span className="text-[10px] font-mono uppercase tracking-widest text-zinc-400 px-3 py-1 block">
            Navigation
          </span>
          <button
            onClick={() => onTabChange("overview")}
            className={cn(
              "w-full flex items-center space-x-3 px-3 py-2 rounded-md text-xs font-medium transition-colors",
              activeTab === "overview"
                ? "bg-white text-black font-bold shadow-sm"
                : "text-zinc-300 hover:text-white hover:bg-zinc-900"
            )}
          >
            <LayoutDashboard className="w-4 h-4 shrink-0" />
            <span>Operations Deck</span>
          </button>

          <button
            onClick={() => onTabChange("hardware")}
            className={cn(
              "w-full flex items-center space-x-3 px-3 py-2 rounded-md text-xs font-medium transition-colors",
              activeTab === "hardware"
                ? "bg-white text-black font-bold shadow-sm"
                : "text-zinc-300 hover:text-white hover:bg-zinc-900"
            )}
          >
            <Cpu className="w-4 h-4 shrink-0" />
            <span>Hardware & Simulation</span>
          </button>

          <button
            onClick={() => onTabChange("diagnostics")}
            className={cn(
              "w-full flex items-center space-x-3 px-3 py-2 rounded-md text-xs font-medium transition-colors",
              activeTab === "diagnostics"
                ? "bg-white text-black font-bold shadow-sm"
                : "text-zinc-300 hover:text-white hover:bg-zinc-900"
            )}
          >
            <Terminal className="w-4 h-4 shrink-0" />
            <span>Diagnostics & Logs</span>
          </button>
        </div>

        {/* Live Subsystems Monitor */}
        <div className="p-4 border-t border-zinc-800/80 space-y-2.5">
          <span className="text-[10px] font-mono uppercase tracking-widest text-zinc-400 block mb-2">
            System Telemetry
          </span>

          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-400">Server Backend</span>
            <div className="flex items-center space-x-1.5 font-mono">
              <span className={`w-1.5 h-1.5 rounded-full ${serverOnline ? "bg-white" : "bg-zinc-600"}`} />
              <span className={serverOnline ? "text-white font-semibold" : "text-zinc-500"}>
                {serverOnline ? "Online" : "Offline"}
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-400">WebSocket Link</span>
            <div className="flex items-center space-x-1.5 font-mono">
              <span className={`w-1.5 h-1.5 rounded-full ${wsConnected ? "bg-white animate-pulse" : "bg-zinc-600"}`} />
              <span className={wsConnected ? "text-white font-semibold" : "text-zinc-500"}>
                {wsConnected ? "Connected" : "Reconnecting"}
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-400">Tracker Process</span>
            <span className="font-mono text-zinc-200">
              {trackerRunning ? `PID ${trackerPid || "—"}` : "Standby"}
            </span>
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-400">Scenario</span>
            <span className="font-mono text-white truncate max-w-[120px]" title={currentScenario}>
              {currentScenario}
            </span>
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-400">Connected Guns</span>
            <span className="font-mono text-white font-bold">
              {connectedGunsCount} / 8
            </span>
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-400">Total Shots</span>
            <span className="font-mono text-white font-bold">
              {totalShotsCount}
            </span>
          </div>
        </div>
      </div>

      {/* Sidebar Footer */}
      <div className="p-4 border-t border-zinc-800 space-y-3">
        <Button
          variant="secondary"
          className="w-full justify-start space-x-2 border-zinc-700 bg-zinc-950 hover:bg-zinc-900 text-zinc-200 hover:text-white"
          onClick={onExitClick}
        >
          <LogOut className="w-4 h-4" />
          <span>Exit Application</span>
        </Button>

        <div className="flex items-center justify-between text-[10px] font-mono text-zinc-500 pt-1">
          <span>Dual Display Active</span>
          <span>B&W Minimalist</span>
        </div>
      </div>
    </aside>
  );
};
