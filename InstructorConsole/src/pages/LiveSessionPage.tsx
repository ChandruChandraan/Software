import React from 'react';
import { Crosshair, Play, Square, Pause, AlertTriangle } from 'lucide-react';

export const LiveSessionPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-800/40 p-5 rounded-2xl border border-slate-700/60">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <Crosshair className="w-5 h-5 text-emerald-400" />
            <span>Live Session Monitor</span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Real-time optical aim tracking, shot impact detection, and range master controls.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button className="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs flex items-center space-x-1.5 transition">
            <Play className="w-3.5 h-3.5" />
            <span>START</span>
          </button>
          <button className="px-3.5 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-semibold text-xs flex items-center space-x-1.5 transition">
            <Pause className="w-3.5 h-3.5" />
            <span>PAUSE</span>
          </button>
          <button className="px-3.5 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs flex items-center space-x-1.5 transition">
            <Square className="w-3.5 h-3.5" />
            <span>STOP</span>
          </button>
          <button className="px-3.5 py-2 rounded-xl bg-red-700 hover:bg-red-600 text-white font-bold text-xs flex items-center space-x-1.5 transition border border-red-500">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>CEASE FIRE</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((lane) => (
          <div key={lane} className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-200 text-sm">LANE {lane}</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-700/60 text-slate-300 font-mono">
                SHOTS: 0 / 10
              </span>
            </div>

            {/* Target Reticle Mock Viewport */}
            <div className="relative aspect-square w-full bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-center overflow-hidden">
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-20">
                <div className="w-3/4 h-3/4 rounded-full border border-slate-400"></div>
                <div className="absolute w-1/2 h-1/2 rounded-full border border-slate-400"></div>
                <div className="absolute w-1/4 h-1/4 rounded-full border border-slate-400"></div>
              </div>
              <div className="w-3 h-3 rounded-full bg-red-500 shadow-lg shadow-red-500/80 animate-ping"></div>
              <span className="text-xs text-slate-600 absolute bottom-2">STANDBY</span>
            </div>

            <div className="text-xs text-slate-400 flex justify-between">
              <span>Score: 0.0</span>
              <span>Gun: Connected</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
