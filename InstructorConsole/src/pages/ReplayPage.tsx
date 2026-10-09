import React from 'react';
import { RotateCcw, Play, SkipBack, SkipForward } from 'lucide-react';

export const ReplayPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="bg-slate-800/40 p-5 rounded-2xl border border-slate-700/60">
        <h2 className="text-xl font-bold text-white flex items-center space-x-2">
          <RotateCcw className="w-5 h-5 text-indigo-400" />
          <span>Shot Replay & Trace Playback</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Review weapon aim trace kinematics 2 seconds pre-shot, trigger break point, and follow-through motion.
        </p>
      </div>

      <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 space-y-4">
        <div className="aspect-video w-full bg-slate-950 rounded-xl border border-slate-800 flex flex-col items-center justify-center">
          <RotateCcw className="w-10 h-10 text-slate-700 mb-2" />
          <p className="text-sm font-semibold text-slate-400">Aim Trace Playback Canvas</p>
          <p className="text-xs text-slate-600">Trace data logged at 120 Hz will render here</p>
        </div>

        {/* Playback Controls */}
        <div className="flex items-center justify-between p-3 bg-slate-900/60 border border-slate-800 rounded-lg">
          <div className="flex items-center space-x-2">
            <button className="p-2 rounded hover:bg-slate-800 text-slate-400"><SkipBack className="w-4 h-4" /></button>
            <button className="p-2 rounded bg-blue-600 hover:bg-blue-500 text-white"><Play className="w-4 h-4" /></button>
            <button className="p-2 rounded hover:bg-slate-800 text-slate-400"><SkipForward className="w-4 h-4" /></button>
          </div>
          <span className="text-xs font-mono text-slate-400">00:00.00 / 00:00.00</span>
        </div>
      </div>
    </div>
  );
};
