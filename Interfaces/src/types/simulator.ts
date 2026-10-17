export interface Gun {
  gun_id: number;
  lane: number;
  connected: boolean;
  port?: string;
  shot_count: number;
  last_seen?: number;
  last_shot_coords?: { x: number; y: number } | null;
}

export interface ShotEvent {
  id?: string;
  type: "shot" | "status";
  gun: number;
  lane: number;
  x: number;
  y: number;
  round: number;
  timestamp: number;
  port?: string;
}

export interface HealthDetails {
  status: string;
  uptime_seconds: number;
  udp_listener?: {
    host: string;
    port: number;
    packets_received: number;
    last_packet_time?: number;
  };
}

export interface ProcessStatus {
  running: boolean;
  pid?: number | null;
  target_path?: string;
  last_error?: string | null;
}

export interface TelemetryStatus {
  freshness: "connected" | "stale" | "disconnected";
  seconds_since_last_event?: number;
  last_valid_event_time?: number | null;
}

export interface UnrealStatus {
  is_running: boolean;
  pid?: number | null;
}

export interface OverlayStatus {
  is_running: boolean;
  pid?: number | null;
  active_identity?: string | null;
}

export interface DisplayInfo {
  index: number;
  width: number;
  height: number;
  is_primary: boolean;
  x: number;
  y: number;
}

export interface Scenario {
  scenario_id: string;
  display_name: string;
  description?: string;
}

export interface LogEntry {
  stream?: "stdout" | "stderr";
  text: string;
  timestamp: number;
}

export interface UdpErrorEntry {
  error: string;
  raw?: string;
  timestamp: number;
}
