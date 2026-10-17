import React from "react";
import { Power } from "lucide-react";

interface ShutdownScreenProps {
  progress: number;
  message: string;
}

export const ShutdownScreen: React.FC<ShutdownScreenProps> = ({ progress, message }) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/95 backdrop-blur-md animate-in fade-in-0">
      <div className="flex flex-col items-center max-w-md w-full px-6 text-center">
        <div className="relative w-24 h-24 mb-6 flex items-center justify-center">
          <div className="absolute inset-0 rounded-full border border-zinc-800" />
          <div className="absolute inset-2 rounded-full border border-zinc-700 animate-pulse-subtle" />
          <div className="absolute inset-6 rounded-full bg-zinc-950 border border-zinc-700 flex items-center justify-center">
            <Power className="w-6 h-6 text-white" />
          </div>
        </div>

        <h1 className="text-xl font-bold tracking-widest text-white mb-2 uppercase font-mono">
          CLOSING SIMULATOR
        </h1>
        <p className="text-xs font-mono text-zinc-400 mb-6 uppercase">
          CLOSING 3D SIMULATOR, TARGET SCREEN & CONNECTED DEVICES
        </p>

        <div className="w-full h-1.5 bg-zinc-900 rounded-full overflow-hidden border border-zinc-800 mb-3">
          <div
            className="h-full bg-white transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>

        <span className="text-xs font-mono text-zinc-400 uppercase tracking-wide">
          {message}
        </span>
      </div>
    </div>
  );
};
