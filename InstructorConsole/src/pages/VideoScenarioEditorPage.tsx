import React from 'react';
import { Film, Plus, Play } from 'lucide-react';

export const VideoScenarioEditorPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-800/40 p-5 rounded-2xl border border-slate-700/60">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <Film className="w-5 h-5 text-rose-400" />
            <span>Branching Video Scenarios</span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Author judgmental shoot/don't shoot video scenarios with hit zones and outcome branches.
          </p>
        </div>
        <button className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition">
          <Plus className="w-4 h-4" />
          <span>Import Video</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[
          { title: 'Traffic Stop Escalation', duration: '2m 14s', branches: 3 },
          { title: 'Commercial Burglary In-Progress', duration: '3m 45s', branches: 4 },
        ].map((item, idx) => (
          <div key={idx} className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-4 flex items-center justify-between">
            <div>
              <h3 className="font-bold text-white text-sm">{item.title}</h3>
              <p className="text-xs text-slate-400 mt-0.5">{item.duration} • {item.branches} Decision Points</p>
            </div>
            <button className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300">
              <Play className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
