import React from 'react';
import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  LayoutDashboard,
  PlaySquare,
  Crosshair,
  BarChart3,
  RotateCcw,
  Users,
  FileSpreadsheet,
  Target,
  Wrench,
  Sliders,
  Film,
  Compass,
  Settings as SettingsIcon,
  LogIn,
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onCloseMobile }) => {
  const { t } = useTranslation();

  const navItems = [
    { to: '/', label: t('dashboard'), icon: LayoutDashboard },
    { to: '/session-setup', label: t('sessionSetup'), icon: PlaySquare },
    { to: '/live-session', label: t('liveSession'), icon: Crosshair },
    { to: '/shot-analysis', label: t('shotAnalysis'), icon: BarChart3 },
    { to: '/replay', label: t('replay'), icon: RotateCcw },
    { to: '/trainees', label: t('trainees'), icon: Users },
    { to: '/reports', label: t('reports'), icon: FileSpreadsheet },
    { to: '/weapons', label: t('weapons'), icon: Target },
    { to: '/target-editor', label: t('targetEditor'), icon: Sliders },
    { to: '/exercise-builder', label: t('exerciseBuilder'), icon: Wrench },
    { to: '/video-scenarios', label: t('videoScenarioEditor'), icon: Film },
    { to: '/calibration', label: t('calibration'), icon: Compass },
    { to: '/settings', label: t('settings'), icon: SettingsIcon },
    { to: '/login', label: t('login'), icon: LogIn },
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 bg-black/60 z-30 lg:hidden"
        />
      )}

      <aside
        className={`fixed lg:static top-16 bottom-0 left-0 w-64 bg-slate-900 border-r border-slate-800 flex flex-col z-40 transition-transform duration-200 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                onClick={onCloseMobile}
                className={({ isActive }) =>
                  `flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span className="truncate">{item.label}</span>
              </NavLink>
            );
          })}
        </div>

        <div className="p-3 border-t border-slate-800 text-xs text-slate-500 text-center">
          v0.1.0-alpha • Simulator Suite
        </div>
      </aside>
    </>
  );
};
