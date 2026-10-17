import React from "react";
import { ShotEvent } from "@/types/simulator";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Activity, Trash2, Target, Crosshair } from "lucide-react";
import { formatTimestamp } from "@/lib/utils";

interface LiveShotFeedProps {
  events: ShotEvent[];
  onClearFeed: () => Promise<void>;
}

export const LiveShotFeed: React.FC<LiveShotFeedProps> = ({ events, onClearFeed }) => {
  // Only display shot events
  const shotEvents = events.filter((e) => e.type === "shot");

  return (
    <div className="space-y-3 flex flex-col h-full">
      {/* Section Header */}
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center space-x-2">
          <Badge variant="outline" className="font-mono text-[10px] bg-zinc-900 border-zinc-700">
            03
          </Badge>
          <h2 className="text-sm font-bold tracking-wider uppercase text-white font-mono flex items-center gap-2">
            <Activity className="w-4 h-4 text-zinc-400" />
            Live Shot Telemetry
          </h2>
        </div>

        <Button
          variant="outline"
          size="xs"
          onClick={onClearFeed}
          className="h-7 text-xs font-mono space-x-1 border-zinc-700 bg-zinc-950 hover:bg-zinc-900 text-zinc-300 hover:text-white"
        >
          <Trash2 className="w-3 h-3" />
          <span>Clear Feed</span>
        </Button>
      </div>

      {/* Feed Card */}
      <div className="rounded-lg border border-zinc-800 bg-zinc-950/80 p-3 overflow-y-auto max-h-[460px] flex-1 shadow-md space-y-2">
        {shotEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center text-zinc-400">
            <div className="w-10 h-10 rounded-full border border-zinc-800 bg-zinc-900 flex items-center justify-center mb-2">
              <Crosshair className="w-5 h-5 text-zinc-500 animate-pulse-subtle" />
            </div>
            <p className="text-xs font-mono font-semibold text-zinc-300">
              Awaiting Ballistic Discharge
            </p>
            <p className="text-[11px] text-zinc-500 max-w-xs mt-1">
              Trigger presses and optical laser pulses will register in this stream in real-time.
            </p>
          </div>
        ) : (
          shotEvents.map((ev, idx) => (
            <div
              key={ev.id || `${ev.timestamp}-${idx}`}
              className="p-3 rounded-md bg-zinc-900/70 border border-zinc-800/90 hover:border-zinc-700 transition-all text-xs"
            >
              {/* Top row */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2 font-mono">
                  <span className="w-2 h-2 rounded-full bg-white animate-ping" />
                  <span className="px-1.5 py-0.5 rounded bg-white text-black font-bold text-[11px]">
                    G{ev.gun}
                  </span>
                  <span className="text-zinc-300 font-semibold">
                    Lane {ev.lane}
                  </span>
                </div>
                <span className="font-mono text-[11px] text-zinc-400">
                  {formatTimestamp(ev.timestamp)}
                </span>
              </div>

              {/* Coordinates & round */}
              <div className="grid grid-cols-2 gap-2 pt-1 border-t border-zinc-800/60 font-mono text-[11px]">
                <div className="flex items-center space-x-1.5 text-zinc-300">
                  <Target className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
                  <span>X:{Math.round(ev.x)} Y:{Math.round(ev.y)}</span>
                </div>
                <div className="text-right text-zinc-400">
                  Shot #{ev.round}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
