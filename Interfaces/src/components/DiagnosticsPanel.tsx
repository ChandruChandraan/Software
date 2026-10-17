import React, { useRef, useEffect, useState } from "react";
import { LogEntry, UdpErrorEntry } from "@/types/simulator";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Terminal, AlertTriangle, Trash2, ArrowDownToLine } from "lucide-react";
import { formatTimestamp } from "@/lib/utils";

interface DiagnosticsPanelProps {
  logs: LogEntry[];
  udpErrors: UdpErrorEntry[];
  onClearLogs?: () => void;
}

export const DiagnosticsPanel: React.FC<DiagnosticsPanelProps> = ({
  logs,
  udpErrors,
  onClearLogs,
}) => {
  const [activeTab, setActiveTab] = useState("logs");
  const [autoScroll, setAutoScroll] = useState(true);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const errorsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll) {
      if (activeTab === "logs") {
        logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
      } else {
        errorsEndRef.current?.scrollIntoView({ behavior: "smooth" });
      }
    }
  }, [logs, udpErrors, activeTab, autoScroll]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold tracking-wider uppercase text-white font-mono flex items-center gap-2 mb-1">
            <Terminal className="w-4 h-4 text-zinc-400" />
            System Diagnostics & Live Stream Logs
          </h2>
          <p className="text-xs text-zinc-400">
            Real-time stdout, stderr, and UDP raw telemetry packet inspection.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            size="xs"
            variant="outline"
            onClick={() => setAutoScroll(!autoScroll)}
            className={`font-mono text-xs border-zinc-700 ${autoScroll ? "bg-white text-black font-bold" : "bg-zinc-950 text-zinc-300"}`}
          >
            <ArrowDownToLine className="w-3 h-3 mr-1" />
            Auto-Scroll: {autoScroll ? "ON" : "OFF"}
          </Button>
          {onClearLogs && (
            <Button
              size="xs"
              variant="outline"
              onClick={onClearLogs}
              className="font-mono text-xs border-zinc-700 bg-zinc-950 hover:bg-zinc-900 text-zinc-300 hover:text-white"
            >
              <Trash2 className="w-3 h-3 mr-1" />
              Clear
            </Button>
          )}
        </div>
      </div>

      <Card className="border-zinc-800 bg-zinc-950/90 shadow-lg">
        <CardHeader className="p-3 border-b border-zinc-800/80">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="bg-zinc-900 border-zinc-800">
              <TabsTrigger value="logs" className="font-mono text-xs space-x-1.5">
                <Terminal className="w-3.5 h-3.5 mr-1" />
                <span>Process Logs</span>
                <Badge variant="outline" className="text-[10px] ml-1 border-zinc-700">
                  {logs.length}
                </Badge>
              </TabsTrigger>
              <TabsTrigger value="errors" className="font-mono text-xs space-x-1.5">
                <AlertTriangle className="w-3.5 h-3.5 mr-1" />
                <span>UDP & Network Exceptions</span>
                <Badge variant={udpErrors.length > 0 ? "white" : "outline"} className="text-[10px] ml-1 font-bold">
                  {udpErrors.length}
                </Badge>
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </CardHeader>

        <CardContent className="p-3">
          {activeTab === "logs" ? (
            <div className="h-96 overflow-y-auto font-mono text-xs p-3 rounded bg-black border border-zinc-900 space-y-1">
              {logs.length === 0 ? (
                <div className="text-zinc-600 text-center py-20">
                  [Awaiting process execution output...]
                </div>
              ) : (
                logs.map((log, idx) => (
                  <div
                    key={idx}
                    className={`leading-relaxed break-all ${
                      log.stream === "stderr"
                        ? "text-zinc-400 font-medium"
                        : "text-zinc-300"
                    }`}
                  >
                    <span className="text-zinc-600 mr-2 select-none">
                      [{formatTimestamp(log.timestamp)}]
                    </span>
                    <span>{log.text}</span>
                  </div>
                ))
              )}
              <div ref={logsEndRef} />
            </div>
          ) : (
            <div className="h-96 overflow-y-auto font-mono text-xs p-3 rounded bg-black border border-zinc-900 space-y-1">
              {udpErrors.length === 0 ? (
                <div className="text-zinc-600 text-center py-20">
                  [No UDP errors or malformed packet payloads detected.]
                </div>
              ) : (
                udpErrors.map((err, idx) => (
                  <div
                    key={idx}
                    className="p-2 rounded bg-zinc-950 border border-zinc-800 text-zinc-300 leading-relaxed mb-2"
                  >
                    <div className="flex justify-between text-zinc-500 mb-1">
                      <span>TIMESTAMP: {formatTimestamp(err.timestamp)}</span>
                      <span className="text-white font-bold">EXCEPTION</span>
                    </div>
                    <div className="text-white font-semibold">{err.error}</div>
                    {err.raw && (
                      <div className="text-zinc-500 text-[11px] mt-1 break-all bg-zinc-900/60 p-1 rounded">
                        RAW: {err.raw}
                      </div>
                    )}
                  </div>
                ))
              )}
              <div ref={errorsEndRef} />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
