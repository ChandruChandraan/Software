import React from 'react';
import { Target, Plus, BatteryCharging, Radio } from 'lucide-react';

export const WeaponsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-800/40 p-5 rounded-2xl border border-slate-700/60">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <Target className="w-5 h-5 text-amber-400" />
            <span>Weapons & Training Units</span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Register simulated firearm platforms, RF dongle pairings, and battery health.
          </p>
        </div>
        <button className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition">
          <Plus className="w-4 h-4" />
          <span>Register Weapon</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { model: 'Glock 17 Gen5', cal: '9x19mm Parabellum', sn: 'WPN-G17-001', battery: 98, status: 'Ready' },
          { model: 'M4A1 Carbine', cal: '5.56x45mm NATO', sn: 'WPN-M4-002', battery: 84, status: 'Ready' },
          { model: 'SIG Sauer P320', cal: '9x19mm Parabellum', sn: 'WPN-P320-003', battery: 92, status: 'Ready' },
        ].map((item, idx) => (
          <div key={idx} className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-bold text-white text-sm">{item.model}</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                {item.status}
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono">{item.sn} • {item.cal}</p>
            <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-xs text-slate-400">
              <span className="flex items-center space-x-1">
                <BatteryCharging className="w-3.5 h-3.5 text-emerald-400" />
                <span>{item.battery}%</span>
              </span>
              <span className="flex items-center space-x-1">
                <Radio className="w-3.5 h-3.5 text-blue-400" />
                <span>RF 2.4GHz</span>
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
