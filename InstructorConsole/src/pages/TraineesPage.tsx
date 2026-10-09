import React from 'react';
import { Users, UserPlus, Search } from 'lucide-react';

export const TraineesPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-800/40 p-5 rounded-2xl border border-slate-700/60">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <Users className="w-5 h-5 text-blue-400" />
            <span>Trainee Roster Management</span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Maintain registered marksmen, squads, historical qualification scores, and certifications.
          </p>
        </div>
        <button className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition">
          <UserPlus className="w-4 h-4" />
          <span>New Trainee</span>
        </button>
      </div>

      <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl overflow-hidden">
        <div className="p-4 border-b border-slate-700/60 flex items-center justify-between">
          <div className="relative w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search service number..."
              className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none"
            />
          </div>
        </div>

        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-900/60 text-slate-400 uppercase font-semibold border-b border-slate-800">
            <tr>
              <th className="px-4 py-3">Service No.</th>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Rank</th>
              <th className="px-4 py-3">Squad / Batch</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            <tr>
              <td className="px-4 py-3 font-mono font-medium text-slate-200">SN-2026-001</td>
              <td className="px-4 py-3">Alex Vance</td>
              <td className="px-4 py-3">Sergeant</td>
              <td className="px-4 py-3">Alpha Squad</td>
              <td className="px-4 py-3 text-right text-blue-400 hover:underline cursor-pointer">Profile</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};
