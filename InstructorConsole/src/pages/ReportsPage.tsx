import React from 'react';
import { FileSpreadsheet, Filter } from 'lucide-react';

export const ReportsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-800/40 p-5 rounded-2xl border border-slate-700/60">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
            <span>Qualification & After-Action Reports</span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Export official qualification scorecards, squad ranking summaries, and ballistics analytics.
          </p>
        </div>
        <button className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-semibold text-xs transition">
          <Filter className="w-4 h-4 text-slate-400" />
          <span>Filter Records</span>
        </button>
      </div>

      <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-8 flex flex-col items-center justify-center text-center">
        <FileSpreadsheet className="w-12 h-12 text-slate-600 mb-3" />
        <h3 className="text-base font-semibold text-slate-200">No Reports Generated Yet</h3>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          Complete a qualification firing course to generate printable certificates and PDF reports.
        </p>
      </div>
    </div>
  );
};
