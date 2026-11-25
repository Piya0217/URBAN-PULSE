// Illustrative records for the Violation Analytics UI. Replace this module with
// a mapper for FastAPI responses when the backend endpoint is available.
export const violationCategories = [
  { name: 'Speeding', severity: 'High', color: '#2dd4c5', base: 46, trend: 8 },
  { name: 'Signal jumping', severity: 'High', color: '#5b91ff', base: 34, trend: 5 },
  { name: 'No helmet', severity: 'Moderate', color: '#f0ad54', base: 28, trend: -3 },
  { name: 'Wrong-side driving', severity: 'Critical', color: '#e17b68', base: 17, trend: 11 },
  { name: 'Other violations', severity: 'Low', color: '#907fe9', base: 22, trend: 2 },
]

export const violationAreas = [
  { name: 'Silk Board', factor: 1.22 },
  { name: 'Marathahalli', factor: 1.14 },
  { name: 'Hebbal', factor: 1.03 },
  { name: 'Whitefield', factor: 0.96 },
  { name: 'Indiranagar', factor: 0.91 },
  { name: 'Yelahanka', factor: 0.78 },
]

const weeklyFactors = [0.74, 0.82, 0.78, 0.87, 0.83, 0.92, 0.88, 0.95, 0.9, 1.04, 0.97, 1.12]

export const demoViolationRecords = weeklyFactors.flatMap((weeklyFactor, weekIndex) => (
  violationAreas.flatMap((area, areaIndex) => violationCategories.flatMap((category, categoryIndex) => {
    // Leave a realistic sample gap so the filter empty state is reachable.
    if (weekIndex === 11 && area.name === 'Yelahanka' && category.name === 'Other violations') return []
    const count = Math.round(category.base * area.factor * weeklyFactor + ((weekIndex + areaIndex * 2 + categoryIndex) % 5))
    return [{
      id: `${weekIndex}-${areaIndex}-${categoryIndex}`,
      week: weekIndex + 1,
      daysAgo: (11 - weekIndex) * 7 + 2,
      area: area.name,
      category: category.name,
      count,
    }]
  }))
))
