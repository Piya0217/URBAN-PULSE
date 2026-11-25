import { useMemo, useState } from 'react'
import { ArrowDownRight, ArrowUpRight, BarChart3, ChevronDown, CircleAlert, Gauge, HardHat, RadioTower, ShieldAlert } from 'lucide-react'
import {
  Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { demoViolationRecords, violationAreas, violationCategories } from '../../data/demoViolations.js'

const kpiDefinitions = [
  { key: 'total', title: 'Total traffic violations', icon: ShieldAlert, tone: 'cyan' },
  { key: 'speeding', title: 'Speeding violations', category: 'Speeding', icon: Gauge, tone: 'blue' },
  { key: 'signal', title: 'Signal jumping violations', category: 'Signal jumping', icon: RadioTower, tone: 'amber' },
  { key: 'helmet', title: 'Helmet violations', category: 'No helmet', icon: HardHat, tone: 'violet' },
]
const tooltipStyle = { background: '#142333', border: '1px solid #2b4354', borderRadius: 8, color: '#edf4fa', fontSize: 10 }
const numberFormat = new Intl.NumberFormat('en-IN')

function DemoTag() {
  return <span className="demo-tag"><span className="demo-dot" />DEMO DATA</span>
}

function FilterSelect({ label, value, onChange, options }) {
  return <label className="violation-filter"><span>{label}</span><select value={value} onChange={(event) => onChange(event.target.value)}>{options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select><ChevronDown size={13} /></label>
}

function MetricCard({ definition, value }) {
  const Icon = definition.icon
  return <article className="kpi-card panel violation-kpi-card"><div className="kpi-card-top"><span className={`kpi-icon icon-${definition.tone}`}><Icon size={18} /></span><DemoTag /></div><div className="kpi-title">{definition.title}</div><div className="kpi-value">{numberFormat.format(value)}</div><div className="kpi-footer"><span className="change-pill down"><span>Illustrative</span></span><span className="kpi-note">sample count</span></div></article>
}

function ChartHeading({ eyebrow, title, subtitle }) {
  return <div className="panel-heading"><div><div className="eyebrow">{eyebrow} <DemoTag /></div><h2>{title}</h2><p>{subtitle}</p></div></div>
}

function ChartEmpty() {
  return <div className="violation-chart-empty"><CircleAlert size={18} /><strong>No matching records</strong><span>Try changing the selected filters.</span></div>
}

function DistributionChart({ data, total }) {
  return <section className="panel violation-chart-card distribution-card">
    <ChartHeading eyebrow="CATEGORY MIX" title="Violation distribution" subtitle="Share of sample violations by category" />
    {total ? <div className="distribution-body"><div className="distribution-donut"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={data} dataKey="count" nameKey="name" innerRadius="66%" outerRadius="91%" paddingAngle={3} cornerRadius={4} stroke="none">{data.map((item) => <Cell key={item.name} fill={item.color} />)}</Pie><Tooltip contentStyle={tooltipStyle} formatter={(value, _name, item) => [`${numberFormat.format(value)} (${item.payload.share}%)`, 'DEMO DATA']} /></PieChart></ResponsiveContainer><div className="distribution-center"><strong>{numberFormat.format(total)}</strong><span>DEMO DATA</span></div></div><div className="distribution-legend">{data.map((item) => <div className="distribution-legend-item" key={item.name}><span><i style={{ background: item.color }} />{item.name}</span><strong>{item.share}%</strong></div>)}</div></div> : <ChartEmpty />}
    <div className="violation-chart-footer"><span>Calculated from active filters</span><span>DEMO DATA</span></div>
  </section>
}

function TrendChart({ data }) {
  return <section className="panel violation-chart-card violation-trend-card">
    <ChartHeading eyebrow="ENFORCEMENT ACTIVITY" title="Weekly violation trend" subtitle="Illustrative sample count by week" />
    {data.length ? <div className="violation-line-chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={data} margin={{ top: 15, right: 10, left: -18, bottom: 0 }}><CartesianGrid stroke="#1c2b3d" strokeDasharray="3 5" vertical={false} /><XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fill: '#718398', fontSize: 9 }} dy={8} /><YAxis axisLine={false} tickLine={false} tick={{ fill: '#718398', fontSize: 9 }} /><Tooltip contentStyle={tooltipStyle} formatter={(value) => [numberFormat.format(value), 'DEMO DATA']} /><Line type="monotone" dataKey="violations" name="Violations" stroke="#35cbbf" strokeWidth={2.5} dot={{ r: 3, fill: '#35cbbf', stroke: '#10202c', strokeWidth: 2 }} activeDot={{ r: 5, fill: '#35cbbf', stroke: '#10202c', strokeWidth: 2 }} /></LineChart></ResponsiveContainer></div> : <ChartEmpty />}
    <div className="violation-chart-footer"><span>Weekly totals follow selected date range</span><span>DEMO DATA</span></div>
  </section>
}

function AreaChartPanel({ data }) {
  return <section className="panel violation-chart-card area-comparison-card">
    <ChartHeading eyebrow="AREA COMPARISON" title="Violations by area" subtitle="Illustrative count across selected Bengaluru areas" />
    {data.length ? <div className="violation-area-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={data} margin={{ top: 13, right: 8, left: -18, bottom: 0 }}><CartesianGrid stroke="#1c2b3d" strokeDasharray="3 5" vertical={false} /><XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#718398', fontSize: 8 }} interval={0} dy={8} /><YAxis axisLine={false} tickLine={false} tick={{ fill: '#718398', fontSize: 9 }} /><Tooltip contentStyle={tooltipStyle} formatter={(value) => [numberFormat.format(value), 'DEMO DATA']} /><Bar dataKey="violations" name="Violations" fill="#4e91f5" radius={[4, 4, 0, 0]} maxBarSize={34} /></BarChart></ResponsiveContainer></div> : <ChartEmpty />}
    <div className="violation-chart-footer"><span>Counts update with all filters</span><span>DEMO DATA</span></div>
  </section>
}

function getTrend(category, records) {
  const weeks = [...new Set(records.map((record) => record.week))].sort((a, b) => b - a)
  if (weeks.length < 2) return { label: '—', direction: 'flat' }
  const [latestWeek, priorWeek] = weeks
  const latest = records.filter((record) => record.week === latestWeek && record.category === category).reduce((sum, record) => sum + record.count, 0)
  const prior = records.filter((record) => record.week === priorWeek && record.category === category).reduce((sum, record) => sum + record.count, 0)
  if (!prior) return { label: 'New', direction: 'up' }
  const change = Math.round(((latest - prior) / prior) * 100)
  return { label: `${change > 0 ? '+' : ''}${change}%`, direction: change > 0 ? 'up' : change < 0 ? 'down' : 'flat' }
}

function ViolationTable({ rows, total, hasRecords }) {
  return <section className="panel violation-table-card">
    <div className="panel-heading violation-table-heading"><div><div className="eyebrow">DETAILED BREAKDOWN <DemoTag /></div><h2>Violation categories</h2><p>Category counts and share within the current selection</p></div><span className="table-result-count">{rows.length} categories</span></div>
    <div className="violation-table-scroll"><table className="violation-table"><thead><tr><th>VIOLATION CATEGORY</th><th>NUMBER OF VIOLATIONS</th><th>PERCENTAGE SHARE</th><th>SEVERITY</th><th>TREND</th></tr></thead><tbody>{hasRecords ? rows.map((row) => {
      const trend = getTrend(row.name, row.records)
      const severityClass = row.severity.toLowerCase().replace(' ', '-')
      return <tr key={row.name}><td><span className="category-color" style={{ background: row.color }} /><strong>{row.name}</strong></td><td className="table-number">{numberFormat.format(row.count)}</td><td><div className="share-cell"><span>{row.share}%</span><i><b style={{ width: `${row.share}%`, background: row.color }} /></i></div></td><td><span className={`violation-severity severity-${severityClass}`}><i />{row.severity}</span></td><td><span className={`violation-trend trend-${trend.direction}`}>{trend.direction === 'up' ? <ArrowUpRight size={13} /> : trend.direction === 'down' ? <ArrowDownRight size={13} /> : null}{trend.label}</span></td></tr>
    }) : <tr><td className="violation-table-empty" colSpan="5"><CircleAlert size={17} /><strong>No violations match these filters</strong><span>Adjust the date range, category, or Bengaluru area.</span></td></tr>}</tbody></table></div>
    <div className="violation-chart-footer"><span>Counts, shares, severities, and trends are illustrative.</span><span>{numberFormat.format(total)} total · DEMO DATA</span></div>
  </section>
}

export default function ViolationAnalytics() {
  const [dateRange, setDateRange] = useState('90')
  const [category, setCategory] = useState('All categories')
  const [area, setArea] = useState('All Bengaluru areas')

  const filteredRecords = useMemo(() => demoViolationRecords.filter((record) => (
    record.daysAgo < Number(dateRange)
    && (category === 'All categories' || record.category === category)
    && (area === 'All Bengaluru areas' || record.area === area)
  )), [dateRange, category, area])

  const total = useMemo(() => filteredRecords.reduce((sum, record) => sum + record.count, 0), [filteredRecords])
  const categoryRows = useMemo(() => violationCategories.map((item) => {
    const records = filteredRecords.filter((record) => record.category === item.name)
    const count = records.reduce((sum, record) => sum + record.count, 0)
    return { ...item, records, count, share: total ? Math.round((count / total) * 100) : 0 }
  }).filter((item) => item.count > 0), [filteredRecords, total])

  const kpis = useMemo(() => kpiDefinitions.map((definition) => ({
    ...definition,
    value: definition.key === 'total' ? total : filteredRecords.filter((record) => record.category === definition.category).reduce((sum, record) => sum + record.count, 0),
  })), [filteredRecords, total])

  const trendData = useMemo(() => [...new Set(filteredRecords.map((record) => record.week))].sort((a, b) => a - b).map((week) => ({
    label: `Week ${week}`,
    violations: filteredRecords.filter((record) => record.week === week).reduce((sum, record) => sum + record.count, 0),
  })), [filteredRecords])

  const areaData = useMemo(() => violationAreas.map((item) => ({
    name: item.name,
    violations: filteredRecords.filter((record) => record.area === item.name).reduce((sum, record) => sum + record.count, 0),
  })).filter((item) => item.violations > 0), [filteredRecords])

  return <div className="page-content violation-page">
    <div className="page-heading violation-page-heading"><div><div className="eyebrow page-eyebrow">CITY INTELLIGENCE <span className="heading-separator">/</span> TRAFFIC ENFORCEMENT</div><h1>Violation Analytics</h1><p>Explore traffic violation patterns and enforcement trends across Bengaluru.</p></div><DemoTag /></div>
    <div className="violation-demo-notice"><CircleAlert size={15} /><span><strong>DEMO DATA</strong> · All values, trends, and area comparisons on this page are illustrative sample data, not actual Bengaluru statistics.</span></div>
    <section className="violation-filters panel"><div className="violation-filter-title"><span><BarChart3 size={15} /></span><div><strong>Filters</strong><small>Update all analytics</small></div></div><FilterSelect label="Date range" value={dateRange} onChange={setDateRange} options={[{ value: '7', label: 'Last 7 days' }, { value: '30', label: 'Last 30 days' }, { value: '90', label: 'Last 90 days' }]} /><FilterSelect label="Violation category" value={category} onChange={setCategory} options={[{ value: 'All categories', label: 'All categories' }, ...violationCategories.map((item) => ({ value: item.name, label: item.name }))]} /><FilterSelect label="Bengaluru area" value={area} onChange={setArea} options={[{ value: 'All Bengaluru areas', label: 'All Bengaluru areas' }, ...violationAreas.map((item) => ({ value: item.name, label: item.name }))]} /><span className="violation-filter-demo"><span className="demo-dot" />Filters use one demo dataset</span></section>
    <div className="kpi-grid violation-kpi-grid">{kpis.map((metric) => <MetricCard key={metric.key} definition={metric} value={metric.value} />)}</div>
    <div className="violation-charts-grid"><DistributionChart data={categoryRows} total={total} /><TrendChart data={trendData} /><AreaChartPanel data={areaData} /></div>
    <ViolationTable rows={categoryRows} total={total} hasRecords={filteredRecords.length > 0} />
    <div className="violation-page-footer"><span>All charts and table rows reflect the active filters.</span><span>DEMO DATA · NOT FOR OPERATIONAL USE</span></div>
  </div>
}
