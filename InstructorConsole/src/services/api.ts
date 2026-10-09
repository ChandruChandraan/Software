import { TrackerStatus, GunTelemetry } from '../types';

const BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://127.0.0.1:8000';

export async function fetchSystemHealth() {
  try {
    const res = await fetch(`${BASE_URL}/system/health`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch (error) {
    return { status: 'offline', service: 'backend', database: 'offline' };
  }
}

export async function fetchLicence() {
  try {
    const res = await fetch(`${BASE_URL}/system/licence`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch (error) {
    return { status: 'offline', licence_type: 'Unknown', seats: 0 };
  }
}

export async function fetchTrainees() {
  const res = await fetch(`${BASE_URL}/trainees/`);
  return res.json();
}

export async function fetchTrackerStatus(): Promise<TrackerStatus> {
  try {
    const res = await fetch(`${BASE_URL}/api/tracker/status`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch (error) {
    return {
      status: 'offline',
      is_active: false,
      host: '127.0.0.1',
      port: 47001,
      total_packets: 0,
      accepted_packets: 0,
      rejected_packets: 0,
      last_packet_time: null,
      has_received_event: false,
      connected_guns: 0,
      total_guns: 0,
      stale_threshold_seconds: 5.0,
    };
  }
}

export async function fetchTrackerGuns(): Promise<GunTelemetry[]> {
  try {
    const res = await fetch(`${BASE_URL}/api/tracker/guns`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const data = await res.json();
    return Array.isArray(data.guns) ? data.guns : [];
  } catch (error) {
    return [];
  }
}
