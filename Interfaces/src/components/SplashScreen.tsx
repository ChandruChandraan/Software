import React, { useEffect, useState, useRef } from "react";
import { Crosshair } from "lucide-react";

interface SplashScreenProps {
  onComplete: () => void;
}

export const SplashScreen: React.FC<SplashScreenProps> = ({ onComplete }) => {
  const [progress, setProgress] = useState(25);
  const [logText, setLogText] = useState("[1/4] Starting communication link...");
  const [fadeOut, setFadeOut] = useState(false);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  const dismiss = () => {
    setFadeOut(true);
    setTimeout(() => {
      onCompleteRef.current();
    }, 300);
  };

  useEffect(() => {
    const steps = [
      { pct: 35, msg: "[1/4] Starting communication link..." },
      { pct: 65, msg: "[2/4] Connecting screens & target display..." },
      { pct: 90, msg: "[3/4] Initializing 3D simulation..." },
      { pct: 100, msg: "[4/4] All systems operational." },
    ];

    let current = 0;
    const interval = setInterval(() => {
      current++;
      if (current < steps.length) {
        setProgress(steps[current].pct);
        setLogText(steps[current].msg);
      } else {
        clearInterval(interval);
        setTimeout(() => {
          setFadeOut(true);
          setTimeout(() => {
            onCompleteRef.current();
          }, 400);
        }, 200);
      }
    }, 250);

    return () => clearInterval(interval);
  }, []); // Run strictly once on mount

  return (
    <div
      onClick={dismiss}
      className={`fixed inset-0 z-50 flex items-center justify-center bg-black cursor-pointer transition-opacity duration-500 ${
        fadeOut ? "opacity-0 pointer-events-none" : "opacity-100"
      }`}
    >
      <div className="flex flex-col items-center max-w-md w-full px-6 text-center select-none">
        {/* Radar Ring Visual */}
        <div className="relative w-28 h-28 mb-8 flex items-center justify-center">
          <div className="absolute inset-0 rounded-full border border-zinc-800 animate-ping opacity-30" />
          <div className="absolute inset-2 rounded-full border border-zinc-700 animate-radar-spin" />
          <div className="absolute inset-5 rounded-full border border-dashed border-zinc-600" />
          <div className="absolute inset-9 rounded-full bg-zinc-900 border border-zinc-700 flex items-center justify-center">
            <Crosshair className="w-6 h-6 text-white" />
          </div>
        </div>

        <h1 className="text-2xl font-bold tracking-widest text-white mb-1 uppercase font-mono">
          FIRINGSIM CONSOLE
        </h1>
        <p className="text-xs font-mono text-zinc-400 tracking-wider mb-8 uppercase">
          MARKSMANSHIP SIMULATOR • BLACK & WHITE EDITION
        </p>

        {/* Progress Bar */}
        <div className="w-full h-1.5 bg-zinc-900 rounded-full overflow-hidden border border-zinc-800 mb-4">
          <div
            className="h-full bg-white transition-all duration-300 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Log Text */}
        <div className="h-6 flex items-center justify-center">
          <span className="text-xs font-mono text-zinc-400 uppercase tracking-wide">
            {logText}
          </span>
        </div>

        <span className="text-[10px] font-mono text-zinc-600 mt-6 uppercase tracking-widest">
          Click or press any key to enter
        </span>
      </div>
    </div>
  );
};
