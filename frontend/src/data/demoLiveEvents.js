// Simulated event stream contract. A FastAPI WebSocket/SSE adapter can later
// map backend messages to this shape without coupling transport to the UI.
export const liveEventCategories = [
  'Accident',
  'Speeding',
  'Traffic congestion',
  'Signal violation',
  'Road blockage',
]

export const liveEventSeverities = ['Low', 'Medium', 'High', 'Critical']
export const liveEventAreas = [
  { name: 'Silk Board', lat: 12.9177, lng: 77.6233 },
  { name: 'Marathahalli', lat: 12.9591, lng: 77.7011 },
  { name: 'Hebbal', lat: 13.0358, lng: 77.597 },
  { name: 'KR Puram', lat: 13.0072, lng: 77.695 },
  { name: 'Whitefield', lat: 12.9698, lng: 77.75 },
  { name: 'Indiranagar', lat: 12.9784, lng: 77.6408 },
  { name: 'Hosur Road', lat: 12.8956, lng: 77.601 },
  { name: 'Yelahanka', lat: 13.1007, lng: 77.5963 },
]

const categoryStatuses = {
  Accident: ['Active', 'Monitoring'],
  Speeding: ['Monitoring', 'Reviewed'],
  'Traffic congestion': ['Monitoring', 'Active'],
  'Signal violation': ['Reviewed', 'Monitoring'],
  'Road blockage': ['Active', 'Monitoring'],
}

export function createSimulatedEvent(id, timestamp = Date.now()) {
  const categoryIndex = Math.floor(Math.random() * liveEventCategories.length)
  const eventType = liveEventCategories[categoryIndex]
  const area = liveEventAreas[Math.floor(Math.random() * liveEventAreas.length)]
  const severity = eventType === 'Accident' && Math.random() > 0.55
    ? 'Critical'
    : liveEventSeverities[Math.floor(Math.random() * liveEventSeverities.length)]
  const statusOptions = categoryStatuses[eventType]

  return {
    id: `SIM-${String(id).padStart(6, '0')}`,
    eventType,
    location: area.name,
    severity,
    timestamp: new Date(timestamp).toISOString(),
    status: statusOptions[Math.floor(Math.random() * statusOptions.length)],
    coordinates: { lat: area.lat, lng: area.lng },
    source: 'simulated-stream',
  }
}

export function createInitialDemoEvents(now = Date.now()) {
  return [
    createSimulatedEvent(1, now - 8 * 60 * 1000),
    createSimulatedEvent(2, now - 16 * 60 * 1000),
    createSimulatedEvent(3, now - 29 * 60 * 1000),
    createSimulatedEvent(4, now - 47 * 60 * 1000),
  ]
}
