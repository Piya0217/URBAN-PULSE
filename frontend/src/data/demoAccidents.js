// Illustrative UI data only. Replace this module with FastAPI response mapping later.
// Coordinates are approximate display points and are not real accident locations.
export const demoAccidentSummary = [
  { title: 'Total reported accidents', value: '1,284', change: '8.2%', direction: 'up', note: 'vs. prior period', icon: 'car', tone: 'cyan' },
  { title: 'Fatal incidents', value: '42', change: '3 fewer', direction: 'down', note: 'vs. prior period', icon: 'fatal', tone: 'amber' },
  { title: 'Severe incidents', value: '186', change: '5.6%', direction: 'up', note: 'vs. prior period', icon: 'severe', tone: 'violet' },
  { title: 'Identified hotspots', value: '18', change: '4 new', direction: 'up', note: 'in selected period', icon: 'hotspot', tone: 'blue' },
]

export const demoHotspots = [
  { id: 1, area: 'Silk Board Junction', zone: 'South Bengaluru', incidents: 86, severity: 'Critical', lat: 12.9177, lng: 77.6233, daysAgo: 2 },
  { id: 2, area: 'Marathahalli Bridge', zone: 'East Bengaluru', incidents: 72, severity: 'High', lat: 12.9591, lng: 77.7011, daysAgo: 5 },
  { id: 3, area: 'Hebbal Flyover', zone: 'North Bengaluru', incidents: 64, severity: 'High', lat: 13.0358, lng: 77.597, daysAgo: 16 },
  { id: 4, area: 'KR Puram Junction', zone: 'East Bengaluru', incidents: 58, severity: 'Moderate', lat: 13.0072, lng: 77.695, daysAgo: 8 },
  { id: 5, area: 'Mysore Road Junction', zone: 'West Bengaluru', incidents: 47, severity: 'Moderate', lat: 12.9567, lng: 77.5482, daysAgo: 28 },
  { id: 6, area: 'Indiranagar 100 Ft Rd', zone: 'Central Bengaluru', incidents: 39, severity: 'Low', lat: 12.9784, lng: 77.6408, daysAgo: 12 },
  { id: 7, area: 'Electronic City Phase 1', zone: 'South Bengaluru', incidents: 34, severity: 'Low', lat: 12.8452, lng: 77.6602, daysAgo: 20 },
  { id: 8, area: 'Yeshwanthpur Circle', zone: 'North Bengaluru', incidents: 29, severity: 'Moderate', lat: 13.0285, lng: 77.5407, daysAgo: 3 },
]

export const demoAccidentTrend = [
  { week: 'Wk 1', incidents: 68 }, { week: 'Wk 2', incidents: 74 },
  { week: 'Wk 3', incidents: 61 }, { week: 'Wk 4', incidents: 86 },
  { week: 'Wk 5', incidents: 79 }, { week: 'Wk 6', incidents: 97 },
  { week: 'Wk 7', incidents: 83 }, { week: 'Wk 8', incidents: 108 },
  { week: 'Wk 9', incidents: 92 }, { week: 'Wk 10', incidents: 116 },
  { week: 'Wk 11', incidents: 103 }, { week: 'Wk 12', incidents: 128 },
]

export const demoAccidentDailyTrend = [
  { week: 'Mon', incidents: 18 }, { week: 'Tue', incidents: 24 },
  { week: 'Wed', incidents: 20 }, { week: 'Thu', incidents: 29 },
  { week: 'Fri', incidents: 25 }, { week: 'Sat', incidents: 34 },
  { week: 'Sun', incidents: 27 },
]
