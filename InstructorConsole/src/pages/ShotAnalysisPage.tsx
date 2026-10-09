import React from 'react';
import { BarChart3, Crosshair, HelpCircle } from 'lucide-react';

export const ShotAnalysisPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="bg-slate-800/40 p-5 rounded-2xl border border-slate-700/60">
        <h2 className="text-xl font-bold text-white flex items-center space-x-2">
          <BarChart3 className="w-5 h-5 text-blue-400" />
          <span>Shot Analysis</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Detailed marksmanship diagnostics: Mean Point of Impact (MPI), grouping dispersion, and trigger pull stability.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 flex flex-col items-center justify-center min-h-[350px]">
          <Crosshair className="w-12 h-12 text-slate-600 mb-2" />
          <p className="text-sm font-semibold text-slate-300">Dispersion Pattern Viewport</p>
          <p className="text-xs text-slate-500 mt-1">Select a completed session to display shot clusters and group metrics</p>
        </div>

        <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center justify-between">
            <span>Diagnostics Summary</span>
            <HelpCircle className="w-4 h-4 text-slate-500" />
          </h3>
          <div className="space-y-2 text-sm text-slate-400">
            <div className="flex justify-between py-2 border-b border-slate-800">
              <span>Mean Point of Impact:</span>
              <span className="font-mono text-slate-200">X: 0.00, Y: 0.00</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-800">
              <span>Extreme Spread:</span>
              <span className="font-mono text-slate-200">0.0 mm</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-800">
              <span>Average Split Time:</span>
              <span className="font-mono text-slate-200">0.00 s</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
