import React from 'react';
import { useTrackerTelemetry } from '../hooks/useTrackerTelemetry';
import {
  Activity,
  Radio,
  Server,
  Crosshair,
  RefreshCw,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Wifi,
  WifiOff,
} from 'lucide-react';

export const TrackerTacticalDashboard: React.FC = () => {
  const {
    trackerStatus,
    guns,
    events,
    wsConnected,
    isLoading,
    refresh,
    clearEvents,
  } = useTrackerTelemetry();

  const formatTimestamp = (timestampSec: number | null): string => {
    if (!timestampSec) return 'None recorded';
    return new Date(timestampSec * 1000).toLocaleTimeString();
  };

  const getStatusBadge = (status: 'online' | 'waiting' | 'offline') => {
    switch (status) {
      case 'online':
        return (
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-950/60 text-emerald-400 border border-emerald-800/80">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>STREAM ACTIVE</span>
          </span>
        );
      case 'waiting':
        return (
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded text-xs font-semibold bg-amber-950/60 text-amber-400 border border-amber-800/80">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
            <span>WAITING TELEMETRY</span>
          </span>
        );
      case 'offline':
      default:
        return (
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded text-xs font-semibold bg-red-950/60 text-red-400 border border-red-800/80">
            <span className="w-1.5 h-1.5 rounded-full bg-red-400"></span>
            <span>OFFLINE</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-4 font-sans text-neutral-200">
      {/* Tactical Header Bar */}
      <div className="bg-black border border-neutral-800 rounded-lg p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded bg-neutral-900 border border-neutral-800 flex items-center justify-center text-neutral-300">
            <Crosshair className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2.5">
              <h3 className="text-sm font-bold uppercase tracking-wider text-neutral-100">
                Tracker Telemetry & UDP Daemon
              </h3>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-neutral-900 border border-neutral-800 text-neutral-400">
                UDP:47001
              </span>
              {getStatusBadge(trackerStatus.status)}
            </div>
            <p className="text-xs text-neutral-500 font-mono mt-0.5">
              Authoritative multi-gun hardware ingestion ? FastAPI backend broadcast
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* WebSocket Link Indicator */}
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-neutral-950 border border-neutral-800 text-xs font-mono">
            {wsConnected ? (
              <>
                <Wifi className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400">WS LIVE</span>
              </>
            ) : (
              <>
                <WifiOff className="w-3.5 h-3.5 text-amber-400" />
                <span className="text-amber-400">WS RECONNECTING</span>
              </>
            )}
          </div>

          <button
            onClick={refresh}
            disabled={isLoading}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded bg-neutral-900 border border-neutral-800 hover:bg-neutral-800 text-xs font-semibold text-neutral-300 hover:text-white transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Sync</span>
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {/* UDP Socket Card */}
        <div className="bg-black border border-neutral-800 rounded-lg p-3">
          <div className="flex items-center justify-between text-neutral-400 mb-1">
            <span className="text-xs font-mono uppercase tracking-wider">UDP Ingestion</span>
            <Server className="w-3.5 h-3.5 text-neutral-500" />
          </div>
          <div className="text-base font-bold text-neutral-100 font-mono">
            {trackerStatus.is_active ? 'BOUND & LISTENING' : 'SOCKET CLOSED'}
          </div>
          <div className="text-xs text-neutral-500 font-mono mt-0.5">
            {trackerStatus.host}:{trackerStatus.port}
          </div>
        </div>

        {/* Packet Counters */}
        <div className="bg-black border border-neutral-800 rounded-lg p-3">
          <div className="flex items-center justify-between text-neutral-400 mb-1">
            <span className="text-xs font-mono uppercase tracking-wider">Packets Ingested</span>
            <Activity className="w-3.5 h-3.5 text-neutral-500" />
          </div>
          <div className="text-base font-bold text-emerald-400 font-mono">
            {trackerStatus.accepted_packets} <span className="text-xs font-normal text-neutral-500">accepted</span>
          </div>
          <div className="text-xs text-neutral-500 font-mono mt-0.5">
            Total: {trackerStatus.total_packets} ? Rejected: {trackerStatus.rejected_packets}
          </div>
        </div>

        {/* Guns Total */}
        <div className="bg-black border border-neutral-800 rounded-lg p-3">
          <div className="flex items-center justify-between text-neutral-400 mb-1">
            <span className="text-xs font-mono uppercase tracking-wider">Gun Units</span>
            <Radio className="w-3.5 h-3.5 text-neutral-500" />
          </div>
          <div className="text-base font-bold text-neutral-100 font-mono">
            <span className="text-emerald-400">{trackerStatus.connected_guns}</span>
            <span className="text-neutral-500"> / {trackerStatus.total_guns} active</span>
          </div>
          <div className="text-xs text-neutral-500 font-mono mt-0.5">
            {trackerStatus.total_guns - trackerStatus.connected_guns} offline or stale
          </div>
        </div>

        {/* Last Packet Time */}
        <div className="bg-black border border-neutral-800 rounded-lg p-3">
          <div className="flex items-center justify-between text-neutral-400 mb-1">
            <span className="text-xs font-mono uppercase tracking-wider">Last Telemetry</span>
            <Crosshair className="w-3.5 h-3.5 text-neutral-500" />
          </div>
          <div className="text-base font-bold text-neutral-100 font-mono">
            {formatTimestamp(trackerStatus.last_packet_time)}
          </div>
          <div className="text-xs text-neutral-500 font-mono mt-0.5">
            Stale limit: {trackerStatus.stale_threshold_seconds}s
          </div>
        </div>
      </div>

      {/* Main Grid: Gun Monitoring & Live Events */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left Column (7 cols): Gun Monitoring Matrix */}
        <div className="lg:col-span-7 bg-black border border-neutral-800 rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-neutral-800/80 pb-2.5">
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-neutral-200">
                Gun Controllers Telemetry Matrix
              </h4>
              <p className="text-xs text-neutral-500 font-mono">
                Live per-lane microcontroller status, assigned COM port, and shot round counters
              </p>
            </div>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-neutral-900 border border-neutral-800 text-neutral-400">
              {guns.length} Units
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono border-collapse">
              <thead>
                <tr className="border-b border-neutral-800 text-neutral-500 text-2xs uppercase tracking-wider">
                  <th className="py-2 px-2.5">Gun ID</th>
                  <th className="py-2 px-2.5">Lane</th>
                  <th className="py-2 px-2.5">Port</th>
                  <th className="py-2 px-2.5">Status</th>
                  <th className="py-2 px-2.5 text-right">Shots</th>
                  <th className="py-2 px-2.5 text-right">Last Seen</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-900/60">
                {guns.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-neutral-500">
                      No gun units reported yet. Ingesting telemetry from Tracker UDP on Port 47001...
                    </td>
                  </tr>
                ) : (
                  guns.map((gun) => {
                    const now = Date.now() / 1000;
                    const elapsed = gun.last_update > 0 ? Math.max(0, Math.round(now - gun.last_update)) : null;

                    return (
                      <tr key={gun.gun_id} className="hover:bg-neutral-950/80 transition-colors">
                        <td className="py-2.5 px-2.5 font-bold text-neutral-200">
                          Gun {gun.gun_id}
                        </td>
                        <td className="py-2.5 px-2.5 text-neutral-400">
                          Lane {gun.lane}
                        </td>
                        <td className="py-2.5 px-2.5 text-neutral-400">
                          {gun.port ? (
                            <span className="text-neutral-300 font-semibold">{gun.port}</span>
                          ) : (
                            <span className="text-neutral-600">?</span>
                          )}
                        </td>
                        <td className="py-2.5 px-2.5">
                          {gun.connected && !gun.is_stale ? (
                            <span className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded bg-emerald-950/70 text-emerald-400 border border-emerald-900 text-2xs font-semibold">
                              <CheckCircle2 className="w-3 h-3" />
                              <span>CONNECTED</span>
                            </span>
                          ) : gun.is_stale ? (
                            <span className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded bg-amber-950/70 text-amber-400 border border-amber-900 text-2xs font-semibold">
                              <AlertTriangle className="w-3 h-3" />
                              <span>STALE (&gt;5s)</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded bg-red-950/70 text-red-400 border border-red-900 text-2xs font-semibold">
                              <XCircle className="w-3 h-3" />
                              <span>OFFLINE</span>
                            </span>
                          )}
                        </td>
                        <td className="py-2.5 px-2.5 text-right font-bold text-neutral-100">
                          {gun.shot_count}
                        </td>
                        <td className="py-2.5 px-2.5 text-right text-neutral-400">
                          {elapsed !== null ? `${elapsed}s ago` : 'Never'}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column (5 cols): Bounded Live Event Stream */}
        <div className="lg:col-span-5 bg-black border border-neutral-800 rounded-lg p-4 space-y-3 flex flex-col">
          <div className="flex items-center justify-between border-b border-neutral-800/80 pb-2.5">
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-neutral-200">
                Live Telemetry Log
              </h4>
              <p className="text-xs text-neutral-500 font-mono">
                WebSocket stream ({events.length} / 50 bounded entries)
              </p>
            </div>
            {events.length > 0 && (
              <button
                onClick={clearEvents}
                className="inline-flex items-center space-x-1 px-2 py-1 rounded bg-neutral-900 hover:bg-neutral-850 text-neutral-400 hover:text-neutral-200 text-2xs border border-neutral-800 transition"
                title="Clear bounded event history"
              >
                <Trash2 className="w-3 h-3" />
                <span>Clear</span>
              </button>
            )}
          </div>

          <div className="flex-1 min-h-[260px] max-h-[360px] overflow-y-auto space-y-1.5 pr-1 font-mono text-xs select-text">
            {events.length === 0 ? (
              <div className="h-full min-h-[240px] flex flex-col items-center justify-center text-center text-neutral-600 p-4 border border-dashed border-neutral-900 rounded">
                <Activity className="w-6 h-6 mb-2 text-neutral-700 animate-pulse" />
                <p className="text-xs font-semibold text-neutral-500">No incoming events yet</p>
                <p className="text-2xs text-neutral-600 mt-0.5">
                  Fired shots and gun connect/disconnect transitions will display here in real-time.
                </p>
              </div>
            ) : (
              events.map((evt) => {
                const isShot = evt.type === 'shot';
                return (
                  <div
                    key={evt.id}
                    className={`p-2 rounded border transition-colors ${
                      isShot
                        ? 'bg-neutral-950/70 border-neutral-800/80'
                        : 'bg-neutral-950/40 border-neutral-850'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-2xs text-neutral-500">
                        {evt.timestamp}
                      </span>
                      <span
                        className={`text-2xs px-1.5 py-0.2 rounded font-semibold ${
                          isShot
                            ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-900/60'
                            : 'bg-neutral-900 text-neutral-300 border border-neutral-800'
                        }`}
                      >
                        {isShot ? 'SHOT' : 'STATUS'}
                      </span>
                    </div>
                    <div className="text-xs text-neutral-300 break-words leading-tight">
                      {evt.summary}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
