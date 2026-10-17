import React from "react";
import { Gun } from "@/types/simulator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { RotateCcw, Crosshair, Target } from "lucide-react";
import { formatTimestamp } from "@/lib/utils";

interface GunsTableProps {
  guns: Gun[];
  onResetShots: () => Promise<void>;
  isResetting?: boolean;
}

export const GunsTable: React.FC<GunsTableProps> = ({ guns, onResetShots, isResetting }) => {
  // Filter for real physical hardware guns
  const physicalGuns = guns
    .filter((g) => g.connected && g.port && !g.port.startsWith("SIM-"))
    .sort((a, b) => a.gun_id - b.gun_id);

  return (
    <div className="space-y-3">
      {/* Section Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Badge variant="outline" className="font-mono text-[10px] bg-zinc-900 border-zinc-700">
            02
          </Badge>
          <h2 className="text-sm font-bold tracking-wider uppercase text-white font-mono flex items-center gap-2">
            <Target className="w-4 h-4 text-zinc-400" />
            Connected Guns
          </h2>
          <Badge variant="secondary" className="font-mono text-xs border-zinc-700">
            {physicalGuns.length} Connected
          </Badge>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={onResetShots}
          disabled={isResetting}
          className="h-8 text-xs font-mono space-x-1.5 border-zinc-700 bg-zinc-950 hover:bg-zinc-900 text-zinc-300 hover:text-white"
        >
          <RotateCcw className={`w-3.5 h-3.5 ${isResetting ? "animate-spin" : ""}`} />
          <span>Reset Shots</span>
        </Button>
      </div>

      {/* Table Container */}
      <div className="rounded-lg border border-zinc-800 bg-zinc-950/80 overflow-hidden shadow-md">
        <Table>
          <TableHeader className="bg-zinc-900/60">
            <TableRow className="border-zinc-800">
              <TableHead className="w-[110px]">GUN</TableHead>
              <TableHead className="w-[100px]">LANE</TableHead>
              <TableHead className="w-[130px]">PORT</TableHead>
              <TableHead className="w-[120px]">STATUS</TableHead>
              <TableHead className="w-[120px]">SHOTS FIRED</TableHead>
              <TableHead>LAST AIM POINT</TableHead>
              <TableHead className="text-right">LAST SEEN</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {physicalGuns.length === 0 ? (
              <TableRow className="border-0">
                <TableCell colSpan={7} className="h-44 text-center">
                  <div className="flex flex-col items-center justify-center space-y-2 py-6 text-zinc-400">
                    <div className="w-12 h-12 rounded-full border border-zinc-800 bg-zinc-900 flex items-center justify-center mb-1">
                      <Crosshair className="w-6 h-6 text-zinc-500 animate-pulse-subtle" />
                    </div>
                    <p className="text-sm font-bold font-mono text-zinc-200">
                      No Hardware Guns Connected
                    </p>
                    <p className="text-xs text-zinc-500 max-w-sm">
                      Plug in recoil or laser simulator pistols via USB to begin automated lane tracking.
                    </p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              physicalGuns.map((gun) => {
                const coords = gun.last_shot_coords
                  ? `${Math.round(gun.last_shot_coords.x)}, ${Math.round(gun.last_shot_coords.y)}`
                  : "—";

                return (
                  <TableRow key={gun.gun_id} className="border-zinc-800/80 hover:bg-zinc-900/40">
                    {/* Gun ID */}
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <span className="px-2 py-0.5 rounded bg-zinc-900 border border-zinc-700 font-mono font-bold text-xs text-white">
                          G{gun.gun_id}
                        </span>
                        <span className="font-mono text-xs text-zinc-400">
                          Gun {gun.gun_id}
                        </span>
                      </div>
                    </TableCell>

                    {/* Lane */}
                    <TableCell>
                      <Badge variant="outline" className="font-mono text-xs border-zinc-700 text-zinc-300">
                        Lane {gun.lane}
                      </Badge>
                    </TableCell>

                    {/* Port */}
                    <TableCell>
                      <span className="font-mono text-xs text-zinc-300">
                        {gun.port || "USB Auto"}
                      </span>
                    </TableCell>

                    {/* Status */}
                    <TableCell>
                      <div className="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded-full bg-zinc-900 border border-zinc-700 text-[11px] font-mono text-white">
                        <span className="w-1.5 h-1.5 rounded-full bg-white" />
                        <span>Online</span>
                      </div>
                    </TableCell>

                    {/* Shots Fired */}
                    <TableCell>
                      <span className="font-mono text-xs font-bold px-2.5 py-1 rounded bg-zinc-900 border border-zinc-700 text-white">
                        {gun.shot_count}
                      </span>
                    </TableCell>

                    {/* Coordinates */}
                    <TableCell>
                      <div className="flex items-center space-x-1.5 font-mono text-xs text-zinc-200">
                        <Crosshair className="w-3.5 h-3.5 text-zinc-400" />
                        <span>{coords}</span>
                      </div>
                    </TableCell>

                    {/* Last Seen */}
                    <TableCell className="text-right font-mono text-xs text-zinc-400">
                      {formatTimestamp(gun.last_seen)}
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};
