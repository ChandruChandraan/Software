import React from 'react';
import { ServiceStatus } from '../types';

interface StatusCardProps {
  title: string;
  status: ServiceStatus;
  subtext?: string;
  icon?: React.ReactNode;
}

export const StatusCard: React.FC<StatusCardProps> = ({ title, status, subtext, icon }) => {
  const getBadgeColor = (st: ServiceStatus) => {
    switch (st) {
      case 'online':
      case 'active':
      case 'calibrated':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'degraded':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'offline':
      default:
        return 'bg-rose-500/20 text-rose-400 border-rose-500/30';
    }
  };

  const getDotColor = (st: ServiceStatus) => {
    switch (st) {
      case 'online':
      case 'active':
      case 'calibrated':
        return 'bg-emerald-400';
      case 'degraded':
        return 'bg-amber-400';
      case 'offline':
      default:
        return 'bg-rose-400';
    }
  };

  return (
    <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-4 shadow-sm hover:border-slate-600 transition-colors">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2 text-slate-300">
          {icon}
          <span className="font-medium text-sm">{title}</span>
        </div>
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border ${getBadgeColor(
            status
          )}`}
        >
          <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${getDotColor(status)}`}></span>
          {status.toUpperCase()}
        </span>
      </div>
      {subtext && <p className="text-xs text-slate-400 mt-1">{subtext}</p>}
    </div>
  );
};
