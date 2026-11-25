import { useEffect, useMemo, useState } from 'react'
import {
  Activity, ArrowDownRight, ArrowUpRight, ChevronDown, CircleAlert,
  Clock3, Eye, Gauge, Lightbulb, ShieldCheck, Siren, TrafficCone,
  UsersRound, WandSparkles,
} from 'lucide-react'
import {
  CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ReferenceLine,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { demoForecasts, demoModelMetrics, demoRecommendations, demoRiskAreas } from '../../data/demoInsights.js'
import { getAccidentInsights } from '../../services/api.js'

const riskColors = { Low: '#35c7b9', Medium: '#a18aef', High: '#f0ad54' }
const tooltipStyle = { background: '#142333', border: '1px solid #2b4354', borderRadius: 8, color: '#edf4fa', fontSize: 10 }
const numberFormat = new Intl.NumberFormat('en-IN')
const decimalFormat = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 })

const INSIGHT_SECTIONS = {
  historical_hotspots: [
    'station', 'zone', 'three_year_crashes', 'three_year_fatal_crashes',
    'average_annual_crashes', 'fatal_crash_percentage',
  ],
  increasing_stations: [
    'station', 'zone', '2023', '2024', '2025',
    'change_2023_to_2025', 'percentage_change',
  ],
  fatality_severity: [
    'station', 'zone', 'fatal_crash_percentage',
    'three_year_crashes', 'three_year_fatal_crashes',
  ],
}

function validateInsightsResponse(response) {
  if (
    response?.status !== 'success' ||
    !response.data ||
    typeof response.data !== 'object' ||
    !response.count ||
    typeof response.count !== 'object'
  ) {
    throw new Error('The historical crash insights API returned an unexpected response.')
  }

  for (const [sectionName, requiredFields] of Object.entries(INSIGHT_SECTIONS)) {
    const rows = response.data[sectionName]
    if (!Array.isArray(rows) || response.count[sectionName] !== rows.length) {
      throw new Error(`The ${sectionName} response is missing or has an invalid count.`)
    }

    const hasInvalidRow = rows.some((row) =>
      !row || typeof row !== 'object' || Array.isArray(row) ||
      requiredFields.some((field) => !Object.prototype.hasOwnProperty.call(row, field))
    )
    if (hasInvalidRow) {
      throw new Error(`The ${sectionName} response contains an invalid record.`)
    }
  }

  return response.data
}

function getNumericValue(value) {
  if (value === null || value === undefined || value === '') return null
  const numericValue = Number(value)
  return Number.isFinite(numericValue) ? numericValue : null
}

function formatNumber(value) {
  const numericValue = getNumericValue(value)
  return numericValue === null ? '\u2014' : numberFormat.format(numericValue)
}

function formatAverage(value) {
  const numericValue = getNumericValue(value)
  return numericValue === null ? '\u2014' : decimalFormat.format(numericValue)
}

function formatPercentage(value, includePositiveSign = false) {
  const numericValue = getNumericValue(value)
  if (numericValue === null) return '\u2014'
  const sign = includePositiveSign && numericValue > 0 ? '+' : ''
  return `${sign}${numericValue.toFixed(2)}%`
}

function DemoTag({ children = 'DEMO DATA' }) {
  return <span className="demo-tag"><span className="demo-dot" />{children}</span>
}

function FilterSelect({ label, value, onChange, options }) {
  return <label className="insight-filter"><span>{label}</span><select value={value} onChange={(event) => onChange(event.target.value)}>{options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select><ChevronDown size={13} /></label>
}

function InsightSummaryCard({ icon: Icon, tone, title, value, detail, status = false, direction }) {
  return <article className="panel insight-summary-card"><div className="insight-summary-top"><span className={`kpi-icon icon-${tone}`}><Icon size={18} /></span><DemoTag /></div><div className="insight-summary-title">{title}</div><div className={`insight-summary-value ${status ? 'insight-status-value' : ''}`}>{value}</div><div className="insight-summary-detail">{direction === 'up' && <ArrowUpRight size={13} />}{direction === 'down' && <ArrowDownRight size={13} />}{detail}</div></article>
}

function PanelHeading({ eyebrow, title, subtitle }) {
  return <div className="panel-heading"><div><div className="eyebrow">{eyebrow} <DemoTag /></div><h2>{title}</h2><p>{subtitle}</p></div></div>
}

function EmptyChart() {
  return <div className="insight-empty"><CircleAlert size={18} /><strong>No sample records match</strong><span>Try another area or risk category.</span></div>
}

function ForecastChart({ data, period, isEmpty }) {
  return <section className="panel insight-chart-card forecast-card"><PanelHeading eyebrow="RISK PROJECTION" title="Illustrative risk forecast" subtitle="Sample risk index across the selected forecast period" />
    {isEmpty ? <EmptyChart /> : <div className="forecast-chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={data} margin={{ top: 14, right: 10, left: -18, bottom: 0 }}><CartesianGrid stroke="#1c2b3d" strokeDasharray="3 5" vertical={false} /><XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fill: '#718398', fontSize: 9 }} dy={8} /><YAxis domain={[0, 100]} ticks={[0, 20, 40, 60, 80, 100]} axisLine={false} tickLine={false} tick={{ fill: '#718398', fontSize: 9 }} /><ReferenceLine y={70} stroke="#e6aa54" strokeDasharray="4 4" label={{ value: 'High risk', position: 'insideTopRight', fill: '#c69858', fontSize: 8 }} /><Tooltip contentStyle={tooltipStyle} formatter={(value) => [`${value} / 100`, 'ILLUSTRATIVE RISK INDEX']} /><Line type="monotone" dataKey="risk" stroke="#43d0c4" strokeWidth={2.5} dot={{ r: 3, fill: '#43d0c4', stroke: '#10202c', strokeWidth: 2 }} activeDot={{ r: 5, fill: '#43d0c4', stroke: '#10202c', strokeWidth: 2 }} /></LineChart></ResponsiveContainer></div>}
    <div className="insight-chart-footer"><span><i className="insight-legend-dot" />Illustrative risk index <span className="risk-threshold-key" />High-risk reference (70)</span><span>{period} forecast · DEMO DATA</span></div>
  </section>
}

function RiskDistribution({ areas }) {
  const distribution = ['Low', 'Medium', 'High'].map((category) => ({ name: category, count: areas.filter((area) => area.category === category).length, color: riskColors[category] })).filter((item) => item.count)
  const total = areas.length
  return <section className="panel insight-chart-card risk-distribution-card"><PanelHeading eyebrow="AREA RISK MIX" title="Risk distribution" subtitle="Illustrative area count by risk category" />
    {total ? <div className="risk-distribution-body"><div className="risk-distribution-donut"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={distribution} dataKey="count" nameKey="name" innerRadius="67%" outerRadius="92%" paddingAngle={4} cornerRadius={4} stroke="none">{distribution.map((item) => <Cell key={item.name} fill={item.color} />)}</Pie><Tooltip contentStyle={tooltipStyle} formatter={(value, name) => [`${value} areas`, `${name} · DEMO DATA`]} /></PieChart></ResponsiveContainer><div className="risk-donut-center"><strong>{total}</strong><span>AREAS</span></div></div><div className="risk-distribution-legend">{distribution.map((item) => <div className="risk-distribution-row" key={item.name}><span><i style={{ background: item.color }} />{item.name} risk</span><strong>{item.count}<small>{total ? ` · ${Math.round(item.count / total * 100)}%` : ''}</small></strong></div>)}</div></div> : <EmptyChart />}
    <div className="insight-chart-footer"><span>Distribution follows active filters</span><span>DEMO DATA</span></div>
  </section>
}

function RiskRankingTable({ areas }) {
  return <section className="panel risk-ranking-card"><div className="panel-heading"><div><div className="eyebrow">PRIORITY LOCATIONS <DemoTag /></div><h2>High-risk area ranking</h2><p>Areas ranked by illustrative risk score</p></div><span className="ranking-count">{areas.length} areas</span></div>
    <div className="risk-table-scroll"><table className="risk-table"><thead><tr><th>AREA</th><th>RISK SCORE <span>/ 100</span></th><th>RISK CATEGORY</th><th>CONTRIBUTING FACTORS</th></tr></thead><tbody>{areas.length ? areas.map((area, index) => <tr key={area.area}><td><span className="risk-rank">{String(index + 1).padStart(2, '0')}</span><strong>{area.area}</strong></td><td><div className="risk-score-cell"><strong>{area.score}</strong><span><i style={{ width: `${area.score}%`, background: riskColors[area.category] }} /></span></div></td><td><span className={`risk-category-chip risk-${area.category.toLowerCase()}`}><i />{area.category}</span></td><td><div className="contributing-factors">{area.factors.map((factor) => <span key={factor}>{factor}</span>)}</div></td></tr>) : <tr><td className="risk-table-empty" colSpan="4"><CircleAlert size={17} /><strong>No areas match your filters</strong><span>Try a different Bengaluru area or risk category.</span></td></tr>}</tbody></table></div>
    <div className="insight-chart-footer"><span>Scores and factors are illustrative sample values.</span><span>DEMO DATA · NOT ACTUAL PREDICTIONS</span></div>
  </section>
}

const historicalColumns = [
  {
    section: 'historical_hotspots',
    title: 'Historical hotspots',
    subtitle: 'Stations ranked by recorded crashes across 2023–2025.',
    columns: [
      { key: 'station', label: 'STATION', format: (value) => value ?? '\u2014' },
      { key: 'zone', label: 'ZONE', format: (value) => value ?? '\u2014' },
      { key: 'three_year_crashes', label: '3-YEAR CRASHES', format: formatNumber },
      { key: 'three_year_fatal_crashes', label: 'FATAL CRASHES', format: formatNumber },
      { key: 'average_annual_crashes', label: 'ANNUAL AVERAGE', format: formatAverage },
      { key: 'fatal_crash_percentage', label: 'FATAL CRASHES (%)', format: formatPercentage },
    ],
    emptyMessage: 'No historical hotspot records are available.',
  },
  {
    section: 'increasing_stations',
    title: 'Increasing station trends',
    subtitle: 'Positive recorded crash changes from 2023 to 2025.',
    columns: [
      { key: 'station', label: 'STATION', format: (value) => value ?? '\u2014' },
      { key: 'zone', label: 'ZONE', format: (value) => value ?? '\u2014' },
      { key: '2023', label: '2023', format: formatNumber },
      { key: '2024', label: '2024', format: formatNumber },
      { key: '2025', label: '2025', format: formatNumber },
      { key: 'change_2023_to_2025', label: 'CHANGE', format: (value) => {
        const numericValue = getNumericValue(value)
        if (numericValue === null) return '\u2014'
        if (numericValue > 0) return `+${formatNumber(numericValue)}`
        return formatNumber(numericValue)
      } },
      { key: 'percentage_change', label: 'CHANGE (%)', format: (value) => formatPercentage(value, true) },
    ],
    emptyMessage: 'No stations with a positive recorded 2023–2025 change are available.',
  },
  {
    section: 'fatality_severity',
    title: 'Fatality severity',
    subtitle: 'Stations ranked by the recorded share of crashes involving fatalities.',
    columns: [
      { key: 'station', label: 'STATION', format: (value) => value ?? '\u2014' },
      { key: 'zone', label: 'ZONE', format: (value) => value ?? '\u2014' },
      { key: 'fatal_crash_percentage', label: 'FATAL CRASHES (%)', format: formatPercentage },
      { key: 'three_year_crashes', label: '3-YEAR CRASHES', format: formatNumber },
      { key: 'three_year_fatal_crashes', label: 'FATAL CRASHES', format: formatNumber },
    ],
    emptyMessage: 'No fatality severity records are available.',
  },
]

function HistoricalInsightTable({ title, subtitle, rows, columns, emptyMessage }) {
  return <section className="panel risk-ranking-card">
    <div className="panel-heading"><div><h2>{title}</h2><p>{subtitle}</p></div><span className="ranking-count">{rows.length} stations</span></div>
    <div className="risk-table-scroll"><table className="risk-table"><thead><tr>{columns.map((column) => <th key={column.key}>{column.label}</th>)}</tr></thead>
      <tbody>{rows.length ? rows.map((row, index) => <tr key={`${row.station}-${row.zone}-${index}`}>
        {columns.map((column) => <td key={column.key}>{column.format(row[column.key])}</td>)}
      </tr>) : <tr><td className="risk-table-empty" colSpan={columns.length}><CircleAlert size={17} /><strong>{emptyMessage}</strong></td></tr>}</tbody>
    </table></div>
    <div className="insight-chart-footer"><span>Historical records from the backend.</span><span>HISTORICAL · NOT A FORECAST</span></div>
  </section>
}

function HistoricalCrashIntelligence({ data, loading, error, onRetry }) {
  return <section className="historical-crash-intelligence">
    <div className="panel-heading"><div><div className="eyebrow">BACKEND HISTORICAL DATA</div><h2>Historical Crash Intelligence</h2><p>Recorded crash analysis for 2023–2025. These historical results are not forecasts or predictions.</p></div><span className="model-preview-badge">BACKEND DATA</span></div>
    {loading && !data && <div className="insight-empty panel" role="status"><Activity size={18} /><strong>Loading historical crash data…</strong></div>}
    {error && <div className="insight-empty panel" role="alert"><CircleAlert size={18} /><strong>Could not load historical crash data</strong><span>{error}</span><button className="stream-button stream-start" onClick={onRetry} disabled={loading}>Retry</button></div>}
    {loading && data && <div className="insight-empty panel" role="status"><Activity size={18} /><span>Refreshing historical crash data…</span></div>}
    {data && <div className="insight-charts-grid">{historicalColumns.map((section) => <HistoricalInsightTable key={section.section} {...section} rows={data[section.section]} />)}</div>}
  </section>
}

function ModelPerformance() {
  return <section className="panel model-performance-card"><div className="panel-heading"><div><div className="eyebrow">MODEL PERFORMANCE <DemoTag /></div><h2>Illustrative evaluation metrics</h2><p>Sample values shown for layout preview only</p></div><span className="model-preview-badge"><WandSparkles size={13} />No trained model connected</span></div>
    <div className="model-metrics-grid">{demoModelMetrics.map((metric) => <article className="model-metric" key={metric.label}><div className="model-metric-top"><span>{metric.label}</span><span className={`model-metric-dot metric-${metric.color}`} /></div><strong>{metric.value}</strong><div className="metric-track"><span className={`metric-fill metric-${metric.color}`} style={{ width: metric.value }} /></div><small>ILLUSTRATIVE · DEMO DATA</small></article>)}</div>
    <div className="model-disclaimer"><CircleAlert size={13} /><span>These are placeholder metrics. No trained ML model generated or validated these values.</span></div>
  </section>
}

const recommendationIcons = { traffic: TrafficCone, visibility: Eye, people: UsersRound }
function Recommendations() {
  return <section className="panel recommendations-card"><div className="panel-heading"><div><div className="eyebrow">ROAD SAFETY ACTIONS <DemoTag /></div><h2>Illustrative recommendations</h2><p>General ideas for review, not operational instructions</p></div><span className="recommendations-icon"><Lightbulb size={16} /></span></div>
    <div className="recommendation-list">{demoRecommendations.map((item, index) => { const Icon = recommendationIcons[item.icon]; return <article className="recommendation-row" key={item.title}><span className={`recommendation-icon recommend-${item.tone}`}><Icon size={17} /></span><div className="recommendation-copy"><div className="recommendation-title-line"><strong>{item.title}</strong><span>{item.tag}</span></div><p>{item.text}</p></div><span className="recommendation-number">0{index + 1}</span></article> })}</div>
    <div className="recommendation-disclaimer"><ShieldCheck size={13} /><span>Illustrative ideas only. Validate with local experts and verified data before acting.</span></div>
  </section>
}

export default function PredictiveInsights() {
  const [period, setPeriod] = useState('30')
  const [areaFilter, setAreaFilter] = useState('All Bengaluru areas')
  const [riskFilter, setRiskFilter] = useState('All risk categories')
  const [historicalData, setHistoricalData] = useState(null)
  const [historicalLoading, setHistoricalLoading] = useState(true)
  const [historicalError, setHistoricalError] = useState('')
  const [retryCount, setRetryCount] = useState(0)

  useEffect(() => {
    let isCurrentRequest = true

    const loadHistoricalInsights = async () => {
      setHistoricalLoading(true)
      setHistoricalError('')
      setHistoricalData(null)
      try {
        const response = await getAccidentInsights()
        const validatedData = validateInsightsResponse(response)
        if (isCurrentRequest) setHistoricalData(validatedData)
      } catch (error) {
        if (isCurrentRequest) {
          setHistoricalError(error.response?.data?.detail || error.message || 'Please try again.')
        }
      } finally {
        if (isCurrentRequest) setHistoricalLoading(false)
      }
    }

    loadHistoricalInsights()
    return () => { isCurrentRequest = false }
  }, [retryCount])

  const filteredAreas = useMemo(() => demoRiskAreas.filter((area) => (
    (areaFilter === 'All Bengaluru areas' || area.area === areaFilter)
    && (riskFilter === 'All risk categories' || area.category === riskFilter)
  )).sort((a, b) => b.score - a.score), [areaFilter, riskFilter])

  const forecast = useMemo(() => {
    if (!filteredAreas.length) return []
    const meanAreaScore = filteredAreas.reduce((sum, area) => sum + area.score, 0) / filteredAreas.length
    const adjustment = meanAreaScore / 58
    return demoForecasts[period].map((point) => ({ ...point, risk: Math.max(0, Math.min(100, Math.round(point.risk * adjustment))) }))
  }, [filteredAreas, period])

  const averageRisk = filteredAreas.length ? Math.round(filteredAreas.reduce((sum, area) => sum + area.score, 0) / filteredAreas.length) : 0
  const highRiskCount = filteredAreas.filter((area) => area.category === 'High').length
  const riskChange = forecast.length > 1 ? forecast.at(-1).risk - forecast[0].risk : 0
  const trendLabel = !filteredAreas.length ? 'No matching areas' : riskChange > 0 ? 'Rising' : riskChange < 0 ? 'Easing' : 'Stable'

  return <div className="page-content insights-page">
    <div className="page-heading insights-page-heading"><div><div className="eyebrow page-eyebrow">CITY INTELLIGENCE <span className="heading-separator">/</span> SAFETY FORECAST</div><h1>Predictive Insights</h1><p>Explore illustrative road-safety risk patterns and forecasting insights across Bengaluru.</p></div><DemoTag /></div>
    <div className="insights-demo-notice"><CircleAlert size={15} /><span><strong>DEMO DATA</strong> · Forecasts, sample risk scores, illustrative area rankings, and model metrics are placeholders. No trained ML model generated those results. The separate Historical Crash Intelligence section uses backend historical analysis.</span></div>
    <section className="insights-filters panel"><div className="insights-filter-title"><span><Activity size={15} /></span><div><strong>Forecast filters</strong><small>Update sample insights</small></div></div><FilterSelect label="Forecast period" value={period} onChange={setPeriod} options={[{ value: '7', label: 'Next 7 days' }, { value: '30', label: 'Next 30 days' }, { value: '90', label: 'Next 90 days' }]} /><FilterSelect label="Bengaluru area" value={areaFilter} onChange={setAreaFilter} options={[{ value: 'All Bengaluru areas', label: 'All Bengaluru areas' }, ...demoRiskAreas.map((area) => ({ value: area.area, label: area.area }))]} /><FilterSelect label="Risk category" value={riskFilter} onChange={setRiskFilter} options={[{ value: 'All risk categories', label: 'All risk categories' }, ...['Low', 'Medium', 'High'].map((risk) => ({ value: risk, label: `${risk} risk` }))]} /><span className="insights-filter-demo"><span className="demo-dot" />Illustrative filters</span></section>
    <div className="insights-summary-grid">
      <InsightSummaryCard icon={Gauge} tone="cyan" title="Overall risk indicator" value={filteredAreas.length ? `${averageRisk} / 100` : '—'} detail="Illustrative average score" />
      <InsightSummaryCard icon={Siren} tone="amber" title="High-risk areas" value={numberFormat.format(highRiskCount)} detail="In the selected area set" />
      <InsightSummaryCard icon={Activity} tone="purple" title="Predicted risk trend" value={trendLabel} detail={forecast.length > 1 ? `${riskChange > 0 ? '+' : ''}${riskChange} points · illustrative` : 'No forecast available'} direction={riskChange > 0 ? 'up' : riskChange < 0 ? 'down' : undefined} />
      <InsightSummaryCard icon={Clock3} tone="blue" title="Model status" value="Preview only" detail="No trained model connected" status />
    </div>
    <div className="insight-charts-grid"><ForecastChart data={forecast} period={`${period} day`} isEmpty={!filteredAreas.length} /><RiskDistribution areas={filteredAreas} /></div>
    <RiskRankingTable areas={filteredAreas} />
    <ModelPerformance />
    <Recommendations />
    <HistoricalCrashIntelligence data={historicalData} loading={historicalLoading} error={historicalError} onRetry={() => setRetryCount((count) => count + 1)} />
    <div className="insights-page-footer"><span><Activity size={13} />Forecast and demo insight values remain illustrative.</span><span>ILLUSTRATIVE · NOT FOR OPERATIONAL USE</span></div>
  </div>
}
