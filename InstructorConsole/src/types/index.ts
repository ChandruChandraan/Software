export type ServiceStatus = 'online' | 'offline' | 'degraded' | 'calibrated' | 'uncalibrated' | 'active';

export interface ServiceHealth {
  id: string;
  name: string;
  status: ServiceStatus;
  description: string;
  lastUpdated?: string;
}

export interface SystemStatusState {
  backend: ServiceStatus;
  tracker: ServiceStatus;
  unreal: ServiceStatus;
  camera: ServiceStatus;
  guns: ServiceStatus;
  projector: ServiceStatus;
  licence: ServiceStatus;
}

export interface AimPoint {
  gun: number;
  lane: number;
  x: number;
  y: number;
  t_us: number;
  frame: number;
}

export interface ShotPoint {
  gun: number;
  lane: number;
  x: number;
  y: number;
  t_us: number;
  score?: number;
  shot_id?: string;
}

export interface TrackerStatus {
  status: 'online' | 'waiting' | 'offline';
  is_active: boolean;
  host: string;
  port: number;
  total_packets: number;
  accepted_packets: number;
  rejected_packets: number;
  last_packet_time: number | null;
  has_received_event: boolean;
  connected_guns: number;
  total_guns: number;
  total_shots?: number;
  unreal_forwarding?: boolean;
  stale_threshold_seconds: number;
}

export interface GunTelemetry {
  gun_id: number;
  lane: number;
  port: string | null;
  connected: boolean;
  raw_connected: boolean;
  shot_count: number;
  last_update: number;
  is_stale: boolean;
}

export interface TrackerEventPayload {
  v?: number;
  type: 'shot' | 'gun_status';
  gun: number;
  lane: number;
  x?: number;
  y?: number;
  display_width?: number;
  display_height?: number;
  round?: number;
  cross_lane?: boolean;
  port?: string | null;
  connected?: boolean;
  shot_count?: number;
  time_us?: number;
}

export interface TrackerWebSocketMessage {
  topic: string;
  payload: TrackerEventPayload;
}

export interface LiveEventItem {
  id: string;
  timestamp: string;
  type: 'shot' | 'gun_status';
  gun: number;
  lane: number;
  summary: string;
  time_us?: number;
  x?: number;
  y?: number;
  round?: number;
  cross_lane?: boolean;
}
