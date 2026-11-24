import { useMemo, useState } from 'react'
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

const riskColors = { Low: '#35c7b9', Medium: '#a18aef', High: '#f0ad54' }
const tooltipStyle = { background: '#142333', border: '1px solid #2b4354', borderRadius: 8, color: '#edf4fa', fontSize: 10 }
const numberFormat = new Intl.NumberFormat('en-IN')

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
    <div className="insights-demo-notice"><CircleAlert size={15} /><span><strong>DEMO DATA</strong> · All risk scores, projections, area rankings, and model metrics are illustrative placeholders. No trained ML model generated these results.</span></div>
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
    <div className="insights-page-footer"><span><Activity size={13} />Sample insight values are isolated for future API integration.</span><span>ILLUSTRATIVE · NOT FOR OPERATIONAL USE</span></div>
  </div>
}
