import React from 'react';
import { Compass, Monitor, Crosshair, CheckCircle2 } from 'lucide-react';

export const CalibrationPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="bg-slate-800/40 p-5 rounded-2xl border border-slate-700/60">
        <h2 className="text-xl font-bold text-white flex items-center space-x-2">
          <Compass className="w-5 h-5 text-emerald-400" />
          <span>System Calibration</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Perform 4-point screen homography mapping and optical weapon zeroing alignments.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Screen Homography */}
        <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
              <Monitor className="w-4 h-4 text-blue-400" />
              <span>Projector Screen Homography</span>
            </h3>
            <span className="inline-flex items-center space-x-1 text-xs text-emerald-400">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Calibrated</span>
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Aligns optical camera pixel coordinates with physical projector display projection boundaries.
          </p>
          <button className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition">
            Launch 4-Corner Calibration Pattern
          </button>
        </div>

        {/* Weapon Zeroing */}
        <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
              <Crosshair className="w-4 h-4 text-amber-400" />
              <span>Optical Weapon Zeroing</span>
            </h3>
            <span className="inline-flex items-center space-x-1 text-xs text-slate-400">
              <span>Ready for Alignment</span>
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Calibrate mechanical sights offset with optical laser beam emission for each training weapon unit.
          </p>
          <button className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-semibold text-xs transition">
            Start 3-Shot Zeroing Sequence
          </button>
        </div>
      </div>
    </div>
  );
};
