import { useState, useEffect, useCallback, useRef } from 'react';
import { TrackerStatus, GunTelemetry, LiveEventItem, TrackerWebSocketMessage } from '../types';
import { fetchTrackerStatus, fetchTrackerGuns } from '../services/api';
import { consoleWs } from '../services/websocket';

const MAX_EVENTS = 50;

export function useTrackerTelemetry() {
  const [trackerStatus, setTrackerStatus] = useState<TrackerStatus>({
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
  });

  const [guns, setGuns] = useState<GunTelemetry[]>([]);
  const [events, setEvents] = useState<LiveEventItem[]>([]);
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const gunsRef = useRef<GunTelemetry[]>([]);
  gunsRef.current = guns;

  const loadSnapshot = useCallback(async () => {
    try {
      const [status, gunsList] = await Promise.all([
        fetchTrackerStatus(),
        fetchTrackerGuns(),
      ]);
      setTrackerStatus(status);
      setGuns(gunsList);
    } catch {
      // Keep previous or fallback
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);

  useEffect(() => {
    // 1. Initial snapshot
    loadSnapshot();

    // 2. Connect WebSocket
    consoleWs.connect();

    const unsubConn = consoleWs.onConnectionChange((connected) => {
      setWsConnected(connected);
      if (connected) {
        // Refresh state upon reconnection
        loadSnapshot();
      }
    });

    // 3. Handle live WebSocket events
    const unsubMsg = consoleWs.subscribe((msg: TrackerWebSocketMessage | any) => {
      if (!msg || msg.topic !== 'tracker_event' || !msg.payload) {
        return;
      }

      const p = msg.payload;
      const nowSec = Date.now() / 1000;
      const eventTimeSec = p.time_us ? p.time_us / 1_000_000 : nowSec;
      const timeStr = new Date(eventTimeSec * 1000).toLocaleTimeString();

      if (p.type === 'shot') {
        const item: LiveEventItem = {
          id: `shot-${p.gun}-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
          timestamp: timeStr,
          type: 'shot',
          gun: p.gun,
          lane: p.lane,
          summary: `Gun ${p.gun} [Lane ${p.lane}] fired (X=${p.x?.toFixed(1) ?? '?'}, Y=${p.y?.toFixed(1) ?? '?'}, Round #${p.round ?? 1})`,
          time_us: p.time_us,
          x: p.x,
          y: p.y,
          round: p.round,
          cross_lane: p.cross_lane,
        };

        setEvents((prev) => [item, ...prev].slice(0, MAX_EVENTS));

        setGuns((prevGuns) => {
          const idx = prevGuns.findIndex((g) => g.gun_id === p.gun);
          if (idx >= 0) {
            const current = prevGuns[idx];
            // Disregard older event if newer update already applied
            if (current.last_update > eventTimeSec) return prevGuns;

            const updated: GunTelemetry = {
              ...current,
              lane: p.lane ?? current.lane,
              connected: true,
              raw_connected: true,
              shot_count: Math.max(current.shot_count, p.round ?? current.shot_count + 1),
              last_update: eventTimeSec,
              is_stale: false,
            };
            const next = [...prevGuns];
            next[idx] = updated;
            return next;
          } else {
            const newGun: GunTelemetry = {
              gun_id: p.gun,
              lane: p.lane ?? p.gun,
              port: null,
              connected: true,
              raw_connected: true,
              shot_count: p.round ?? 1,
              last_update: eventTimeSec,
              is_stale: false,
            };
            return [...prevGuns, newGun].sort((a, b) => a.gun_id - b.gun_id);
          }
        });

        setTrackerStatus((prev) => ({
          ...prev,
          status: 'online',
          accepted_packets: prev.accepted_packets + 1,
          total_packets: prev.total_packets + 1,
          last_packet_time: eventTimeSec,
          has_received_event: true,
        }));
      } else if (p.type === 'gun_status') {
        const statusLabel = p.connected ? 'Connected' : 'Disconnected';
        const portLabel = p.port ? ` on ${p.port}` : '';
        const item: LiveEventItem = {
          id: `status-${p.gun}-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
          timestamp: timeStr,
          type: 'gun_status',
          gun: p.gun,
          lane: p.lane,
          summary: `Gun ${p.gun} [Lane ${p.lane}] ${statusLabel}${portLabel}`,
          time_us: p.time_us,
        };

        setEvents((prev) => [item, ...prev].slice(0, MAX_EVENTS));

        setGuns((prevGuns) => {
          const idx = prevGuns.findIndex((g) => g.gun_id === p.gun);
          const isConnected = Boolean(p.connected);

          if (idx >= 0) {
            const current = prevGuns[idx];
            if (current.last_update > eventTimeSec) return prevGuns;

            const updated: GunTelemetry = {
              ...current,
              lane: p.lane ?? current.lane,
              port: p.port !== undefined ? p.port : current.port,
              connected: isConnected,
              raw_connected: isConnected,
              shot_count: p.shot_count !== undefined ? Math.max(current.shot_count, p.shot_count) : current.shot_count,
              last_update: eventTimeSec,
              is_stale: false,
            };
            const next = [...prevGuns];
            next[idx] = updated;
            return next;
          } else {
            const newGun: GunTelemetry = {
              gun_id: p.gun,
              lane: p.lane ?? p.gun,
              port: p.port ?? null,
              connected: isConnected,
              raw_connected: isConnected,
              shot_count: p.shot_count ?? 0,
              last_update: eventTimeSec,
              is_stale: false,
            };
            return [...prevGuns, newGun].sort((a, b) => a.gun_id - b.gun_id);
          }
        });

        setTrackerStatus((prev) => ({
          ...prev,
          status: 'online',
          accepted_packets: prev.accepted_packets + 1,
          total_packets: prev.total_packets + 1,
          last_packet_time: eventTimeSec,
          has_received_event: true,
        }));
      }
    });

    // 4. Stale checker interval (every 1s)
    const interval = setInterval(() => {
      const now = Date.now() / 1000;
      setGuns((prevGuns) => {
        let changed = false;
        const next = prevGuns.map((g) => {
          const isStale = g.raw_connected && (now - g.last_update > trackerStatus.stale_threshold_seconds);
          const effectiveConnected = g.raw_connected && !isStale;
          if (g.is_stale !== isStale || g.connected !== effectiveConnected) {
            changed = true;
            return { ...g, is_stale: isStale, connected: effectiveConnected };
          }
          return g;
        });
        return changed ? next : prevGuns;
      });

      // Update connected gun count and stream vitality
      setTrackerStatus((prev) => {
        const activeCount = gunsRef.current.filter((g) => g.connected && !g.is_stale).length;
        const isOnline = prev.is_active && prev.last_packet_time !== null && (now - prev.last_packet_time <= prev.stale_threshold_seconds);
        const nextStatus = isOnline ? 'online' : (prev.is_active ? 'waiting' : 'offline');

        if (prev.connected_guns !== activeCount || prev.status !== nextStatus || prev.total_guns !== gunsRef.current.length) {
          return {
            ...prev,
            connected_guns: activeCount,
            total_guns: gunsRef.current.length,
            status: nextStatus,
          };
        }
        return prev;
      });
    }, 1000);

    return () => {
      unsubConn();
      unsubMsg();
      clearInterval(interval);
    };
  }, [loadSnapshot, trackerStatus.stale_threshold_seconds]);

  return {
    trackerStatus,
    guns,
    events,
    wsConnected,
    isLoading,
    refresh: loadSnapshot,
    clearEvents,
  };
}
