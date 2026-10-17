import React, { useState } from "react";
import { Scenario } from "@/types/simulator";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Layers, Loader2, AlertCircle, CheckCircle2 } from "lucide-react";

interface ScenarioSelectorProps {
  scenarios: Scenario[];
  currentScenario: string;
  onScenarioChange: (scenarioId: string) => Promise<void>;
}

export const ScenarioSelector: React.FC<ScenarioSelectorProps> = ({
  scenarios,
  currentScenario,
  onScenarioChange,
}) => {
  const [selectedId, setSelectedId] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Default to first scenario or match current
  React.useEffect(() => {
    if (scenarios.length > 0 && !selectedId) {
      const match = scenarios.find((s) => s.display_name === currentScenario);
      setSelectedId(match ? match.scenario_id : scenarios[0].scenario_id);
    }
  }, [scenarios, currentScenario, selectedId]);

  const handleChange = async () => {
    if (!selectedId) return;
    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      await onScenarioChange(selectedId);
      const target = scenarios.find((s) => s.scenario_id === selectedId);
      setSuccessMessage(`Switched scenario to: ${target?.display_name || selectedId}`);
      setTimeout(() => setSuccessMessage(null), 3500);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to change scenario";
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const selectedScenarioObj = scenarios.find((s) => s.scenario_id === selectedId);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Badge variant="outline" className="font-mono text-[10px] bg-zinc-900 border-zinc-700">
            01
          </Badge>
          <h2 className="text-sm font-bold tracking-wider uppercase text-white font-mono flex items-center gap-2">
            <Layers className="w-4 h-4 text-zinc-400" />
            Scenario Configuration
          </h2>
        </div>
        <span className="text-xs text-zinc-400">
          Live 3D Level Coordinator
        </span>
      </div>

      <Card className="border-zinc-800 bg-zinc-950/80">
        <CardContent className="p-4 sm:p-5">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
            {/* Current Active Scenario */}
            <div className="md:col-span-4 p-3 rounded-lg bg-zinc-900/80 border border-zinc-800">
              <span className="text-[10px] font-mono text-zinc-400 uppercase tracking-wider block mb-1">
                Active Simulator Level
              </span>
              <div className="text-sm font-mono font-bold text-white flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
                <span className="truncate">{currentScenario || "Indoor Shooting Range"}</span>
              </div>
            </div>

            {/* Selector Dropdown */}
            <div className="md:col-span-5">
              <label className="text-[10px] font-mono text-zinc-400 uppercase tracking-wider block mb-1.5">
                Select Scenario
              </label>
              <div className="relative">
                <select
                  value={selectedId}
                  onChange={(e) => setSelectedId(e.target.value)}
                  disabled={isLoading || scenarios.length === 0}
                  className="w-full h-10 px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-md text-xs font-mono text-white focus:outline-none focus:border-white transition-colors cursor-pointer disabled:opacity-50"
                >
                  {scenarios.length === 0 ? (
                    <option value="">No scenarios discovered</option>
                  ) : (
                    scenarios.map((sc) => (
                      <option key={sc.scenario_id} value={sc.scenario_id}>
                        {sc.display_name}
                      </option>
                    ))
                  )}
                </select>
              </div>
            </div>

            {/* Change Action Button */}
            <div className="md:col-span-3 flex items-end">
              <Button
                onClick={handleChange}
                disabled={isLoading || !selectedId || scenarios.length === 0}
                className="w-full h-10 text-xs font-mono uppercase tracking-wider font-bold"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" />
                    Updating...
                  </>
                ) : (
                  "Change Scenario"
                )}
              </Button>
            </div>
          </div>

          {/* Description Snippet */}
          {selectedScenarioObj?.description && (
            <div className="mt-3 pt-3 border-t border-zinc-800/60 text-xs text-zinc-400 font-mono">
              <span className="text-zinc-500 uppercase text-[10px] mr-2">Overview:</span>
              {selectedScenarioObj.description}
            </div>
          )}

          {/* Success Banner */}
          {successMessage && (
            <div className="mt-3 p-2.5 rounded bg-zinc-900 border border-zinc-700 text-xs text-zinc-200 flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-white shrink-0" />
              <span>{successMessage}</span>
            </div>
          )}

          {/* Error Banner */}
          {errorMessage && (
            <div className="mt-3 p-2.5 rounded bg-zinc-950 border border-zinc-700 text-xs text-zinc-300 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 text-white shrink-0" />
                <span>{errorMessage}</span>
              </div>
              <button
                onClick={() => setErrorMessage(null)}
                className="text-zinc-500 hover:text-white text-xs font-mono ml-4"
              >
                ✕
              </button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
