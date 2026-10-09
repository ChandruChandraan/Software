import React from 'react';
import { Wrench, Plus } from 'lucide-react';

export const ExerciseBuilderPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-800/40 p-5 rounded-2xl border border-slate-700/60">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <Wrench className="w-5 h-5 text-cyan-400" />
            <span>Exercise & Course Builder</span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Construct structured marksmanship drills with exposure times, round limits, and distances.
          </p>
        </div>
        <button className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition">
          <Plus className="w-4 h-4" />
          <span>New Drill</span>
        </button>
      </div>

      <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-8 text-center">
        <Wrench className="w-12 h-12 text-slate-600 mx-auto mb-3" />
        <h3 className="text-base font-semibold text-slate-200">Interactive Drill Timeline Builder</h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
          Visual sequence orchestrator for configuring turning targets, popup delays, and scoring windows.
        </p>
      </div>
    </div>
  );
};
