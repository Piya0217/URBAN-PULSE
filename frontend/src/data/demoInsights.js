// Illustrative UI data only. These forecasts and model metrics are not produced
// by a trained model; replace this module with FastAPI response mapping later.
export const demoRiskAreas = [
  { area: 'Silk Board Junction', score: 91, category: 'High', factors: ['Peak-hour congestion', 'Frequent signal conflicts'] },
  { area: 'Marathahalli Bridge', score: 86, category: 'High', factors: ['High traffic volume', 'Mixed road users'] },
  { area: 'Hebbal Flyover', score: 82, category: 'High', factors: ['Complex merge lanes', 'Limited visibility'] },
  { area: 'KR Puram Junction', score: 72, category: 'High', factors: ['Road works', 'Peak-hour congestion'] },
  { area: 'Hosur Road', score: 64, category: 'Medium', factors: ['High traffic volume', 'Mixed road users'] },
  { area: 'Whitefield Main Road', score: 58, category: 'Medium', factors: ['Road works', 'Night visibility'] },
  { area: 'Indiranagar 100 Ft Rd', score: 43, category: 'Medium', factors: ['Mixed road users', 'Peak-hour congestion'] },
  { area: 'Yelahanka New Town', score: 28, category: 'Low', factors: ['Night visibility', 'Road works'] },
  { area: 'Jayanagar 4th Block', score: 19, category: 'Low', factors: ['Mixed road users', 'Night visibility'] },
]

export const demoForecasts = {
  '7': [
    { label: 'Today', risk: 47 }, { label: 'Tue', risk: 50 }, { label: 'Wed', risk: 48 },
    { label: 'Thu', risk: 56 }, { label: 'Fri', risk: 62 }, { label: 'Sat', risk: 58 }, { label: 'Sun', risk: 66 },
  ],
  '30': [
    { label: 'Wk 1', risk: 42 }, { label: 'Wk 2', risk: 47 }, { label: 'Wk 3', risk: 51 },
    { label: 'Wk 4', risk: 49 }, { label: 'Wk 5', risk: 59 }, { label: 'Wk 6', risk: 64 },
  ],
  '90': [
    { label: 'Wk 1', risk: 38 }, { label: 'Wk 2', risk: 42 }, { label: 'Wk 3', risk: 40 },
    { label: 'Wk 4', risk: 46 }, { label: 'Wk 5', risk: 44 }, { label: 'Wk 6', risk: 51 },
    { label: 'Wk 7', risk: 49 }, { label: 'Wk 8', risk: 55 }, { label: 'Wk 9', risk: 53 },
    { label: 'Wk 10', risk: 61 }, { label: 'Wk 11', risk: 58 }, { label: 'Wk 12', risk: 66 },
  ],
}

export const demoModelMetrics = [
  { label: 'Accuracy', value: '87.4%', color: 'cyan' },
  { label: 'Precision', value: '82.1%', color: 'blue' },
  { label: 'Recall', value: '79.6%', color: 'purple' },
  { label: 'F1-score', value: '80.8%', color: 'amber' },
]

export const demoRecommendations = [
  { icon: 'traffic', tone: 'cyan', title: 'Review signal timing', text: 'Consider a signal timing review at the highest ranked sample junctions during peak periods.', tag: 'INTERSECTION SAFETY' },
  { icon: 'visibility', tone: 'purple', title: 'Improve night visibility', text: 'Review lighting and reflective road markings around the sample areas with low visibility factors.', tag: 'ROAD INFRASTRUCTURE' },
  { icon: 'people', tone: 'amber', title: 'Plan targeted road-user awareness', text: 'Consider focused safety messaging where mixed road users appear among the illustrative factors.', tag: 'COMMUNITY SAFETY' },
]
