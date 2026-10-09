import React from 'react';
import { useTranslation } from 'react-i18next';
import { useStatus } from '../hooks/useStatus';
import { StatusCard } from '../components/StatusCard';
import { TrackerTacticalDashboard } from '../components/TrackerTacticalDashboard';
import {
  Server,
  Crosshair,
  Gamepad2,
  Camera,
  Radio,
  Projector,
  KeyRound,
  RefreshCw,
  Users,
  Target,
  Clock,
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { t } = useTranslation();
  const { statuses, refresh } = useStatus();

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-neutral-950 p-5 rounded-xl border border-neutral-800">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white">
            {t('dashboard')}
          </h2>
          <p className="text-sm text-neutral-400 mt-0.5">
            Real-time status overview of simulator subsystems and connected lanes.
          </p>
        </div>
        <button
          onClick={refresh}
          className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-neutral-900 text-neutral-200 border border-neutral-800 hover:bg-neutral-800 text-sm font-semibold transition"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh Services</span>
        </button>
      </div>

      {/* Centerpiece: Pure-Black Tactical Tracker & Gun Monitoring Dashboard */}
      <TrackerTacticalDashboard />

      {/* Service Health Grid */}
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-3">
          Subsystem Diagnostics
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <StatusCard
            title={t('services.backend')}
            status={statuses.backend}
            subtext="FastAPI Server & SQLite DB (Port 8000)"
            icon={<Server className="w-4 h-4 text-blue-400" />}
          />
          <StatusCard
            title={t('services.tracker')}
            status={statuses.tracker}
            subtext="Optical Marksmanship Daemon (UDP 47000/47001)"
            icon={<Crosshair className="w-4 h-4 text-emerald-400" />}
          />
          <StatusCard
            title={t('services.unreal')}
            status={statuses.unreal}
            subtext="3D Ballistics & Virtual Range Engine"
            icon={<Gamepad2 className="w-4 h-4 text-purple-400" />}
          />
          <StatusCard
            title={t('services.camera')}
            status={statuses.camera}
            subtext="120 FPS High-Speed Optical Capture"
            icon={<Camera className="w-4 h-4 text-cyan-400" />}
          />
          <StatusCard
            title={t('services.guns')}
            status={statuses.guns}
            subtext="Wireless RF Trigger Transceiver"
            icon={<Radio className="w-4 h-4 text-amber-400" />}
          />
          <StatusCard
            title={t('services.projector')}
            status={statuses.projector}
            subtext="Display Homography Calibration"
            icon={<Projector className="w-4 h-4 text-indigo-400" />}
          />
          <StatusCard
            title={t('services.licence')}
            status={statuses.licence}
            subtext="Enterprise Qualification Suite (16 Seats)"
            icon={<KeyRound className="w-4 h-4 text-rose-400" />}
          />
        </div>
      </div>

      {/* Quick Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="bg-black border border-neutral-800 rounded-lg p-4 flex items-center space-x-4">
          <div className="w-10 h-10 rounded bg-neutral-900 border border-neutral-800 flex items-center justify-center text-blue-400">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs font-medium text-neutral-400 uppercase tracking-wider font-mono">Active Trainees</p>
            <p className="text-xl font-bold text-white mt-0.5">0 / 8 Lanes</p>
          </div>
        </div>

        <div className="bg-black border border-neutral-800 rounded-lg p-4 flex items-center space-x-4">
          <div className="w-10 h-10 rounded bg-neutral-900 border border-neutral-800 flex items-center justify-center text-emerald-400">
            <Target className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs font-medium text-neutral-400 uppercase tracking-wider font-mono">Current Course</p>
            <p className="text-lg font-bold text-white mt-0.5">None Selected</p>
          </div>
        </div>

        <div className="bg-black border border-neutral-800 rounded-lg p-4 flex items-center space-x-4">
          <div className="w-10 h-10 rounded bg-neutral-900 border border-neutral-800 flex items-center justify-center text-amber-400">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs font-medium text-neutral-400 uppercase tracking-wider font-mono">Session Status</p>
            <p className="text-lg font-bold text-white mt-0.5">Standby</p>
          </div>
        </div>
      </div>
    </div>
  );
};
