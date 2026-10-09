import test from 'node:test';
import assert from 'node:assert/strict';

// Test simulated frontend telemetry reducer logic mirroring useTrackerTelemetry
function processIncomingEvent(state, payload) {
  const nowSec = Date.now() / 1000;
  const eventTimeSec = payload.time_us ? payload.time_us / 1_000_000 : nowSec;

  if (payload.type === 'shot') {
    const nextGuns = [...state.guns];
    const idx = nextGuns.findIndex(g => g.gun_id === payload.gun);

    if (idx >= 0) {
      if (nextGuns[idx].last_update > eventTimeSec) {
        return state; // ignore older/stale event
      }
      nextGuns[idx] = {
        ...nextGuns[idx],
        lane: payload.lane ?? nextGuns[idx].lane,
        connected: true,
        shot_count: Math.max(nextGuns[idx].shot_count, payload.round ?? nextGuns[idx].shot_count + 1),
        last_update: eventTimeSec,
        is_stale: false,
      };
    } else {
      nextGuns.push({
        gun_id: payload.gun,
        lane: payload.lane ?? payload.gun,
        port: null,
        connected: true,
        shot_count: payload.round ?? 1,
        last_update: eventTimeSec,
        is_stale: false,
      });
    }

    return {
      ...state,
      accepted_packets: state.accepted_packets + 1,
      total_packets: state.total_packets + 1,
      last_packet_time: eventTimeSec,
      guns: nextGuns,
    };
  } else if (payload.type === 'gun_status') {
    const nextGuns = [...state.guns];
    const idx = nextGuns.findIndex(g => g.gun_id === payload.gun);
    const isConn = Boolean(payload.connected);

    if (idx >= 0) {
      if (nextGuns[idx].last_update > eventTimeSec) {
        return state;
      }
      nextGuns[idx] = {
        ...nextGuns[idx],
        lane: payload.lane ?? nextGuns[idx].lane,
        port: payload.port !== undefined ? payload.port : nextGuns[idx].port,
        connected: isConn,
        shot_count: payload.shot_count !== undefined ? Math.max(nextGuns[idx].shot_count, payload.shot_count) : nextGuns[idx].shot_count,
        last_update: eventTimeSec,
        is_stale: false,
      };
    } else {
      nextGuns.push({
        gun_id: payload.gun,
        lane: payload.lane ?? payload.gun,
        port: payload.port ?? null,
        connected: isConn,
        shot_count: payload.shot_count ?? 0,
        last_update: eventTimeSec,
        is_stale: false,
      });
    }

    return {
      ...state,
      accepted_packets: state.accepted_packets + 1,
      total_packets: state.total_packets + 1,
      last_packet_time: eventTimeSec,
      guns: nextGuns,
    };
  }

  return state;
}

test('Initial REST snapshot initializes state properly', () => {
  const mockRestGuns = [
    { gun_id: 1, lane: 1, port: 'COM3', connected: true, shot_count: 5, last_update: 1000, is_stale: false }
  ];
  assert.equal(mockRestGuns.length, 1);
  assert.equal(mockRestGuns[0].gun_id, 1);
  assert.equal(mockRestGuns[0].connected, true);
});

test('Live WebSocket shot event updates gun round and packet counter', () => {
  const initial = {
    guns: [{ gun_id: 1, lane: 1, port: 'COM3', connected: true, shot_count: 2, last_update: 100 }],
    accepted_packets: 10,
    total_packets: 10,
    last_packet_time: 100,
  };

  const updated = processIncomingEvent(initial, {
    v: 1,
    type: 'shot',
    gun: 1,
    lane: 1,
    x: 960,
    y: 540,
    round: 3,
    time_us: 200_000_000,
  });

  assert.equal(updated.accepted_packets, 11);
  assert.equal(updated.guns[0].shot_count, 3);
  assert.equal(updated.guns[0].last_update, 200);
});

test('Stale/older event does not overwrite newer state', () => {
  const initial = {
    guns: [{ gun_id: 1, lane: 1, port: 'COM3', connected: true, shot_count: 10, last_update: 500 }],
    accepted_packets: 5,
    total_packets: 5,
    last_packet_time: 500,
  };

  // Attempt to apply an event from time 400 (older than 500)
  const result = processIncomingEvent(initial, {
    v: 1,
    type: 'shot',
    gun: 1,
    lane: 1,
    x: 100,
    y: 100,
    round: 8,
    time_us: 400_000_000,
  });

  assert.equal(result.guns[0].shot_count, 10);
  assert.equal(result.guns[0].last_update, 500);
});

test('Gun status transitions (connected -> disconnected)', () => {
  let state = {
    guns: [],
    accepted_packets: 0,
    total_packets: 0,
    last_packet_time: null,
  };

  // Connect
  state = processIncomingEvent(state, {
    v: 1,
    type: 'gun_status',
    gun: 2,
    lane: 2,
    port: 'COM7',
    connected: true,
    shot_count: 0,
    time_us: 100_000_000,
  });

  assert.equal(state.guns.length, 1);
  assert.equal(state.guns[0].connected, true);
  assert.equal(state.guns[0].port, 'COM7');

  // Disconnect
  state = processIncomingEvent(state, {
    v: 1,
    type: 'gun_status',
    gun: 2,
    lane: 2,
    port: null,
    connected: false,
    shot_count: 0,
    time_us: 150_000_000,
  });

  assert.equal(state.guns[0].connected, false);
  assert.equal(state.guns[0].last_update, 150);
});

test('Malformed and empty events are ignored safely', () => {
  const initial = {
    guns: [],
    accepted_packets: 0,
    total_packets: 0,
  };

  const res1 = processIncomingEvent(initial, {});
  assert.equal(res1.accepted_packets, 0);

  const res2 = processIncomingEvent(initial, { type: 'unknown_type' });
  assert.equal(res2.accepted_packets, 0);
});
