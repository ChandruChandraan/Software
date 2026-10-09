import React from 'react';
import { Settings as SettingsIcon, Save, Server } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="bg-slate-800/40 p-5 rounded-2xl border border-slate-700/60">
        <h2 className="text-xl font-bold text-white flex items-center space-x-2">
          <SettingsIcon className="w-5 h-5 text-slate-400" />
          <span>System Settings</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Network endpoints, telemetry UDP ports, security policies, and simulator preferences.
        </p>
      </div>

      <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-6 space-y-6 max-w-2xl">
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
            <Server className="w-4 h-4 text-blue-400" />
            <span>Network & Ports</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Backend Host</label>
              <input
                type="text"
                defaultValue="127.0.0.1"
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Backend HTTP Port</label>
              <input
                type="number"
                defaultValue={8000}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Tracker UDP Port (Unreal)</label>
              <input
                type="number"
                defaultValue={47000}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Tracker UDP Port (Backend)</label>
              <input
                type="number"
                defaultValue={47001}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200"
              />
            </div>
          </div>
        </div>

        <button className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition">
          <Save className="w-4 h-4" />
          <span>Save Configuration</span>
        </button>
      </div>
    </div>
  );
};
