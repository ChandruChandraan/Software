import React from 'react';
import { Sliders, Plus, Circle } from 'lucide-react';

export const TargetEditorPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-800/40 p-5 rounded-2xl border border-slate-700/60">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <Sliders className="w-5 h-5 text-indigo-400" />
            <span>Target Geometry & Scoring Zones</span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Create and customize target dimensions, scoring rings, and hit zones.
          </p>
        </div>
        <button className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition">
          <Plus className="w-4 h-4" />
          <span>New Target Layout</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-6 flex flex-col items-center justify-center min-h-[300px]">
          <Circle className="w-24 h-24 text-slate-700" />
          <p className="text-sm font-semibold text-slate-300 mt-3">Target Canvas Preview</p>
          <p className="text-xs text-slate-500">Interactive polygon & ring editor placeholder</p>
        </div>

        <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
            Target Presets
          </h3>
          <div className="space-y-2">
            {['Standard ISSF 25m Precision', 'Military Silhouette Type E', 'Steel Falling Popper', 'Tactical Hostage No-Shoot'].map((t, idx) => (
              <div key={idx} className="p-3 bg-slate-900/60 border border-slate-800 rounded-lg flex items-center justify-between">
                <span className="text-sm text-slate-200">{t}</span>
                <button className="text-xs text-blue-400 hover:underline">Edit</button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
