import React from 'react';
import { useTranslation } from 'react-i18next';
import { Globe, Shield, Menu } from 'lucide-react';

interface HeaderProps {
  onToggleSidebar?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onToggleSidebar }) => {
  const { t, i18n } = useTranslation();

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
  };

  return (
    <header className="h-16 bg-slate-900/90 border-b border-slate-800 px-4 md:px-6 flex items-center justify-between sticky top-0 z-30 backdrop-blur">
      <div className="flex items-center space-x-3">
        <button
          onClick={onToggleSidebar}
          className="p-2 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 lg:hidden"
          title="Toggle Navigation"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div className="flex items-center space-x-2.5">
          <div className="w-9 h-9 rounded-lg bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight text-slate-100 leading-none">
              {t('appTitle')}
            </h1>
            <p className="text-xs text-slate-400 font-medium hidden sm:block">
              {t('tagline')}
            </p>
          </div>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {/* Language selector */}
        <div className="flex items-center space-x-1.5 bg-slate-800/80 px-2.5 py-1.5 rounded-lg border border-slate-700/60 text-xs text-slate-300">
          <Globe className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={i18n.language}
            onChange={(e) => changeLanguage(e.target.value)}
            className="bg-transparent border-none text-slate-200 focus:outline-none cursor-pointer pr-1"
          >
            <option value="en" className="bg-slate-800 text-slate-200">EN</option>
            <option value="hi" className="bg-slate-800 text-slate-200">HI (हिन्दी)</option>
            <option value="fr" className="bg-slate-800 text-slate-200">FR (Français)</option>
          </select>
        </div>

        {/* User profile indicator */}
        <div className="flex items-center space-x-2 pl-2 border-l border-slate-800">
          <div className="w-8 h-8 rounded-full bg-slate-700 border border-slate-600 flex items-center justify-center text-xs font-bold text-slate-200">
            IN
          </div>
          <span className="text-sm font-medium text-slate-300 hidden md:inline">
            Instructor Lead
          </span>
        </div>
      </div>
    </header>
  );
};
