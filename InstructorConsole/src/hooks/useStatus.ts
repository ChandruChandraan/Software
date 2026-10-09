import { useState, useEffect } from 'react';
import { fetchSystemHealth, fetchLicence, fetchTrackerStatus } from '../services/api';
import { SystemStatusState } from '../types';

export function useStatus() {
  const [statuses, setStatuses] = useState<SystemStatusState>({
    backend: 'offline',
    tracker: 'offline',
    unreal: 'offline',
    camera: 'online',
    guns: 'offline',
    projector: 'calibrated',
    licence: 'active',
  });

  const checkHealth = async () => {
    const [health, licence, tracker] = await Promise.all([
      fetchSystemHealth(),
      fetchLicence(),
      fetchTrackerStatus(),
    ]);

    setStatuses((prev) => ({
      ...prev,
      backend: health.status === 'ok' ? 'online' : 'offline',
      licence: licence.status === 'active' ? 'active' : 'offline',
      tracker: tracker.status === 'online' ? 'online' : (tracker.status === 'waiting' ? 'degraded' : 'offline'),
      guns: tracker.connected_guns > 0 ? 'online' : 'offline',
    }));
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  return { statuses, refresh: checkHealth };
}
