import React from 'react';
import { PlaySquare, Users, Crosshair } from 'lucide-react';

export const SessionSetupPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="bg-slate-800/40 p-5 rounded-2xl border border-slate-700/60">
        <h2 className="text-xl font-bold text-white flex items-center space-x-2">
          <PlaySquare className="w-5 h-5 text-blue-400" />
          <span>Session Setup</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Configure lane roster, trainee assignments, and exercise course before firing begins.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
            <Users className="w-4 h-4 text-blue-400" />
            <span>Lane Trainee Allocation</span>
          </h3>
          <div className="space-y-3">
            {[1, 2, 3, 4].map((lane) => (
              <div key={lane} className="flex items-center justify-between p-3 bg-slate-900/60 border border-slate-800 rounded-lg">
                <span className="font-semibold text-slate-300 text-sm">Lane {lane}</span>
                <span className="text-xs text-slate-500 italic">Unassigned (Standby)</span>
                <button className="text-xs px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-blue-400 font-medium border border-slate-700">
                  Assign Trainee
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
            <Crosshair className="w-4 h-4 text-emerald-400" />
            <span>Qualification Course Selection</span>
          </h3>
          <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-lg space-y-2">
            <p className="text-sm font-medium text-slate-200">Standard Military Marksmanship Stage 1</p>
            <p className="text-xs text-slate-400">10 Shots • 25 Meters • Standing Unsupported • Bullseye Target</p>
          </div>
          <button className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm transition shadow-lg shadow-blue-600/30">
            Initialize & Arm Range
          </button>
        </div>
      </div>
    </div>
  );
};
