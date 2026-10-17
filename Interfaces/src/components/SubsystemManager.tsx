import React from "react";
import {
  ProcessStatus,
  TelemetryStatus,
  UnrealStatus,
  OverlayStatus,
  DisplayInfo,
} from "@/types/simulator";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Play, Square, RotateCw, Monitor, Crosshair, Layers, Cpu } from "lucide-react";

interface SubsystemManagerProps {
  trackerProcess: ProcessStatus | null;
  telemetry: TelemetryStatus | null;
  unrealStatus: UnrealStatus | null;
  overlayStatus: OverlayStatus | null;
  displays: DisplayInfo[];
  onStartTracker: () => Promise<void>;
  onStopTracker: () => Promise<void>;
  onRestartTracker: () => Promise<void>;
  onStartUnreal: () => Promise<void>;
  onStopUnreal: () => Promise<void>;
  onStartOverlay: () => Promise<void>;
  onStopOverlay: () => Promise<void>;
}

export const SubsystemManager: React.FC<SubsystemManagerProps> = ({
  trackerProcess,
  telemetry,
  unrealStatus,
  overlayStatus,
  displays,
  onStartTracker,
  onStopTracker,
  onRestartTracker,
  onStartUnreal,
  onStopUnreal,
  onStartOverlay,
  onStopOverlay,
}) => {
  const isTrackerRunning = !!trackerProcess?.running;
  const isUnrealRunning = !!unrealStatus?.is_running;
  const isOverlayRunning = !!overlayStatus?.is_running;

  const primaryDisplay = displays.find((d) => d.is_primary) || displays[0];
  const secondaryDisplay = displays.find((d) => !d.is_primary);
  const targetDisplay = secondaryDisplay || primaryDisplay;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-sm font-bold tracking-wider uppercase text-white font-mono flex items-center gap-2 mb-1">
          <Cpu className="w-4 h-4 text-zinc-400" />
          Hardware & Process Management
        </h2>
        <p className="text-xs text-zinc-400">
          Core services orchestrating laser tracking, 3D Unreal Engine simulation, and multi-display target screens.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {/* Tracker Service Card */}
        <Card className="border-zinc-800 bg-zinc-950/80">
          <CardHeader className="pb-3 border-b border-zinc-800/80 flex flex-row items-center justify-between">
            <div className="flex items-center space-x-2">
              <Crosshair className="w-4 h-4 text-white" />
              <CardTitle className="text-xs font-mono uppercase tracking-wider">
                Tracker Engine
              </CardTitle>
            </div>
            <Badge
              variant={isTrackerRunning ? "white" : "outline"}
              className="text-[10px] font-mono"
            >
              {isTrackerRunning ? "RUNNING" : "STOPPED"}
            </Badge>
          </CardHeader>
          <CardContent className="pt-4 space-y-3">
            <div className="space-y-1.5 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-zinc-500">PID:</span>
                <span className="text-zinc-200">{trackerProcess?.pid || "—"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Telemetry:</span>
                <span className="text-zinc-200 uppercase">{telemetry?.freshness || "Standby"}</span>
              </div>
              <div className="flex justify-between truncate">
                <span className="text-zinc-500 mr-2">Path:</span>
                <span className="text-zinc-400 truncate max-w-[170px]" title={trackerProcess?.target_path || ""}>
                  {trackerProcess?.target_path || "Default"}
                </span>
              </div>
            </div>

            <div className="pt-2 grid grid-cols-3 gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={onStartTracker}
                disabled={isTrackerRunning}
                className="text-xs font-mono border-zinc-700 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 hover:text-white"
              >
                <Play className="w-3 h-3 mr-1" />
                Start
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={onStopTracker}
                disabled={!isTrackerRunning}
                className="text-xs font-mono border-zinc-700 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 hover:text-white"
              >
                <Square className="w-3 h-3 mr-1" />
                Stop
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={onRestartTracker}
                className="text-xs font-mono border-zinc-700 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 hover:text-white"
              >
                <RotateCw className="w-3 h-3 mr-1" />
                Reset
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* 3D Unreal Engine Simulation Card */}
        <Card className="border-zinc-800 bg-zinc-950/80">
          <CardHeader className="pb-3 border-b border-zinc-800/80 flex flex-row items-center justify-between">
            <div className="flex items-center space-x-2">
              <Layers className="w-4 h-4 text-white" />
              <CardTitle className="text-xs font-mono uppercase tracking-wider">
                Unreal Engine
              </CardTitle>
            </div>
            <Badge
              variant={isUnrealRunning ? "white" : "outline"}
              className="text-[10px] font-mono"
            >
              {isUnrealRunning ? "ACTIVE" : "OFFLINE"}
            </Badge>
          </CardHeader>
          <CardContent className="pt-4 space-y-3">
            <div className="space-y-1.5 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-zinc-500">Process ID:</span>
                <span className="text-zinc-200">{unrealStatus?.pid || "—"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Output Target:</span>
                <span className="text-zinc-200">
                  {targetDisplay ? `Display ${targetDisplay.index}` : "Primary"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">FPS / Render:</span>
                <span className="text-zinc-400">60 FPS Hardware V-Sync</span>
              </div>
            </div>

            <div className="pt-2 grid grid-cols-2 gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={onStartUnreal}
                disabled={isUnrealRunning}
                className="text-xs font-mono border-zinc-700 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 hover:text-white"
              >
                <Play className="w-3 h-3 mr-1" />
                Launch 3D
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={onStopUnreal}
                disabled={!isUnrealRunning}
                className="text-xs font-mono border-zinc-700 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 hover:text-white"
              >
                <Square className="w-3 h-3 mr-1" />
                Stop
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Projector Target Screen Overlay Card */}
        <Card className="border-zinc-800 bg-zinc-950/80">
          <CardHeader className="pb-3 border-b border-zinc-800/80 flex flex-row items-center justify-between">
            <div className="flex items-center space-x-2">
              <Monitor className="w-4 h-4 text-white" />
              <CardTitle className="text-xs font-mono uppercase tracking-wider">
                Target Screen Overlay
              </CardTitle>
            </div>
            <Badge
              variant={isOverlayRunning ? "white" : "outline"}
              className="text-[10px] font-mono"
            >
              {isOverlayRunning ? "PROJECTING" : "STANDBY"}
            </Badge>
          </CardHeader>
          <CardContent className="pt-4 space-y-3">
            <div className="space-y-1.5 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-zinc-500">Overlay PID:</span>
                <span className="text-zinc-200">{overlayStatus?.pid || "—"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Screen Output:</span>
                <span className="text-zinc-200">
                  {overlayStatus?.active_identity || (secondaryDisplay ? `Display ${secondaryDisplay.index}` : "Primary")}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Calibration:</span>
                <span className="text-zinc-400">Locked 4-Point Homography</span>
              </div>
            </div>

            <div className="pt-2 grid grid-cols-2 gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={onStartOverlay}
                disabled={isOverlayRunning}
                className="text-xs font-mono border-zinc-700 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 hover:text-white"
              >
                <Play className="w-3 h-3 mr-1" />
                Start Screen
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={onStopOverlay}
                disabled={!isOverlayRunning}
                className="text-xs font-mono border-zinc-700 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 hover:text-white"
              >
                <Square className="w-3 h-3 mr-1" />
                Close Screen
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Connected Displays & Projector Specs */}
      <Card className="border-zinc-800 bg-zinc-950/80">
        <CardHeader className="pb-3 border-b border-zinc-800/80 flex flex-row items-center justify-between">
          <CardTitle className="text-xs font-mono uppercase tracking-wider flex items-center gap-2">
            <Monitor className="w-4 h-4 text-zinc-400" />
            Detected Display Topology & Projector Resolution
          </CardTitle>
          <Badge variant="outline" className="text-xs font-mono border-zinc-700">
            {displays.length} Screens Identified
          </Badge>
        </CardHeader>
        <CardContent className="pt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800 font-mono text-xs space-y-1">
              <div className="flex justify-between font-bold text-white mb-1">
                <span>Display 1 (Primary Console)</span>
                <span className="text-[10px] uppercase text-zinc-400">Desktop App</span>
              </div>
              <p className="text-zinc-400">
                Resolution: {primaryDisplay ? `${primaryDisplay.width}×${primaryDisplay.height}` : "1920×1080"}
              </p>
              <p className="text-zinc-500 text-[11px]">
                Coordinates: ({primaryDisplay?.x || 0}, {primaryDisplay?.y || 0})
              </p>
            </div>

            <div className="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800 font-mono text-xs space-y-1">
              <div className="flex justify-between font-bold text-white mb-1">
                <span>Display 2 (Simulator Target Projector)</span>
                <span className="text-[10px] uppercase text-zinc-400">Unreal / Overlay</span>
              </div>
              <p className="text-zinc-400">
                Resolution: {secondaryDisplay ? `${secondaryDisplay.width}×${secondaryDisplay.height}` : "None Detected (Mirrored)"}
              </p>
              <p className="text-zinc-500 text-[11px]">
                Coordinates: ({secondaryDisplay?.x || 0}, {secondaryDisplay?.y || 0})
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
