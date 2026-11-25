import { useEffect, useMemo, useState } from 'react'
import { MapContainer, Marker, Popup, TileLayer, Tooltip as MapTooltip, ZoomControl, useMap } from 'react-leaflet'
import L from 'leaflet'
import {
  Activity, AlertOctagon, ArrowDownRight, ArrowUpRight, CarFront,
  ChevronDown, CircleAlert, Crosshair, Filter, MapPin, Maximize2,
  ShieldAlert, SlidersHorizontal, Target,
} from 'lucide-react'
import {
  Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { demoAccidentDailyTrend, demoAccidentSummary, demoAccidentTrend, demoHotspots } from '../../data/demoAccidents.js'

const iconByName = { car: CarFront, fatal: AlertOctagon, severe: ShieldAlert, hotspot: Target }
const severityStyles = { Critical: 'critical', High: 'high', Moderate: 'moderate', Low: 'low' }
const areaOptions = ['All Bengaluru areas', ...new Set(demoHotspots.map((hotspot) => hotspot.zone))]

function MetricCard({ metric }) {
  const Icon = iconByName[metric.icon]
  return <article className="kpi-card panel accident-kpi">
    <div className="kpi-card-top"><span className={`kpi-icon icon-${metric.tone}`}><Icon size={18} /></span><span className="demo-tag"><span className="demo-dot" />DEMO DATA</span></div>
    <div className="kpi-title">{metric.title}</div>
    <div className="kpi-value">{metric.value}</div>
    <div className="kpi-footer"><span className={`change-pill ${metric.direction}`}><span>{metric.direction === 'up' ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}{metric.change}</span></span><span className="kpi-note">{metric.note}</span></div>
  </article>
}

function makeMarkerIcon(severity) {
  const type = severityStyles[severity] || 'moderate'
  return L.divIcon({
    className: 'accident-marker-shell',
    html: `<span class="accident-marker accident-marker-${type}"><span></span></span>`,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  })
}

function MapResizeHandler() {
  const map = useMap()
  useEffect(() => {
    const timer = window.setTimeout(() => map.invalidateSize(), 150)
    return () => window.clearTimeout(timer)
  }, [map])
  return null
}

function AccidentMap({ hotspots }) {
  return <section className="panel accident-map-card">
    <div className="map-card-heading"><div><div className="eyebrow">GEOSPATIAL VIEW <span className="demo-tag"><span className="demo-dot" />DEMO DATA</span></div><h2>Illustrative accident hotspots</h2><p>Sample points placed for interface preview only</p></div><button className="map-action" title="Map view" aria-label="Map view"><Maximize2 size={15} /></button></div>
    <div className="map-frame">
      <MapContainer center={[12.9716, 77.5946]} zoom={11} zoomControl={false} dragging={true} scrollWheelZoom className="accident-map" aria-label="Interactive map of Bengaluru with illustrative accident hotspots">
        <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <ZoomControl position="bottomright" />
        <MapResizeHandler />
        {hotspots.map((hotspot) => <Marker key={hotspot.id} position={[hotspot.lat, hotspot.lng]} icon={makeMarkerIcon(hotspot.severity)}>
          <MapTooltip direction="top" offset={[0, -10]}>{hotspot.area} <span>· DEMO DATA</span></MapTooltip>
          <Popup><div className="map-popup"><strong>{hotspot.area}</strong><span>{hotspot.incidents} illustrative incidents</span><span>Severity: {hotspot.severity} · DEMO DATA</span></div></Popup>
        </Marker>)}
      </MapContainer>
      <div className="map-demo-note"><CircleAlert size={14} /><span><strong>DEMO DATA</strong> · Markers show illustrative sample points, not actual accident locations.</span></div>
      <div className="map-legend"><span>Severity</span><i className="legend-critical" />Critical<i className="legend-high" />High<i className="legend-moderate" />Moderate<i className="legend-low" />Low</div>
      <div className="map-count"><MapPin size={13} />{hotspots.length} sample hotspots</div>
    </div>
  </section>
}

function AccidentTrend({ days }) {
  const data = days === '7' ? demoAccidentDailyTrend : days === '30' ? demoAccidentTrend.slice(-5) : demoAccidentTrend
  const interval = data.length > 6 ? 1 : 0
  return <section className="panel accident-trend-card">
    <div className="panel-heading"><div><div className="eyebrow">INCIDENT HISTORY <span className="demo-tag"><span className="demo-dot" />DEMO DATA</span></div><h2>Accident trend</h2><p>Illustrative reported incidents by {days === '7' ? 'day' : 'week'}</p></div><span className="trend-period"><Activity size={13} />{days === '7' ? '7 days' : days === '30' ? '30 days' : '90 days'}</span></div>
    <div className="trend-chart"><ResponsiveContainer width="100%" height="100%"><AreaChart data={data} margin={{ top: 10, right: 5, left: -22, bottom: 0 }}>
      <defs><linearGradient id="accidentTrendFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#f0aa54" stopOpacity={0.25} /><stop offset="100%" stopColor="#f0aa54" stopOpacity={0.01} /></linearGradient></defs>
      <CartesianGrid stroke="#1c2b3d" strokeDasharray="3 5" vertical={false} />
      <XAxis dataKey="week" interval={interval} axisLine={false} tickLine={false} tick={{ fill: '#697c92', fontSize: 10 }} dy={8} />
      <YAxis axisLine={false} tickLine={false} tick={{ fill: '#697c92', fontSize: 10 }} />
      <Tooltip contentStyle={{ background: '#142333', border: '1px solid #2b4354', borderRadius: 8, color: '#edf4fa', fontSize: 11 }} formatter={(value) => [`${value} incidents`, 'DEMO DATA']} />
      <Area type="monotone" dataKey="incidents" stroke="#f0ae59" strokeWidth={2} fill="url(#accidentTrendFill)" activeDot={{ r: 4, fill: '#f0ae59', stroke: '#0d1826', strokeWidth: 2 }} />
    </AreaChart></ResponsiveContainer></div>
    <div className="trend-footer"><span>Weekly sample trend</span><span>Source: isolated demo dataset</span></div>
  </section>
}

function HotspotTable({ hotspots }) {
  return <section className="panel hotspot-table-card">
    <div className="panel-heading hotspot-table-heading"><div><div className="eyebrow">PRIORITY AREAS <span className="demo-tag"><span className="demo-dot" />DEMO DATA</span></div><h2>Hotspot ranking</h2><p>Ranked by illustrative incident count</p></div><button className="table-sort" title="Sorted by incident count"><SlidersHorizontal size={14} /> Highest count <ChevronDown size={13} /></button></div>
    <div className="hotspot-table-scroll"><table className="hotspot-table"><thead><tr><th>RANK / AREA</th><th>ZONE</th><th>INCIDENTS <span>DEMO</span></th><th>SEVERITY</th></tr></thead><tbody>
      {hotspots.length ? hotspots.map((hotspot, index) => <tr key={hotspot.id}><td><span className="rank-number">{String(index + 1).padStart(2, '0')}</span><span className="table-area"><strong>{hotspot.area}</strong><small><MapPin size={11} />Illustrative sample area</small></span></td><td className="table-zone">{hotspot.zone}</td><td><strong className="incident-count">{hotspot.incidents}</strong></td><td><span className={`severity-pill severity-${severityStyles[hotspot.severity]}`}><i />{hotspot.severity}</span></td></tr>) : <tr><td colSpan="4" className="empty-hotspots">No sample hotspots match these filters.</td></tr>}
    </tbody></table></div>
    <div className="table-footnote"><span><CircleAlert size={13} />All counts and rankings are illustrative demo values.</span><span>Showing {hotspots.length} of {demoHotspots.length} sample areas</span></div>
  </section>
}

export default function AccidentIntelligence() {
  const [dateRange, setDateRange] = useState('90')
  const [severity, setSeverity] = useState('All severities')
  const [area, setArea] = useState('All Bengaluru areas')

  const filteredHotspots = useMemo(() => demoHotspots.filter((hotspot) => {
    const withinRange = dateRange === '90' || (hotspot.daysAgo ?? 0) <= Number(dateRange)
    const matchesSeverity = severity === 'All severities' || hotspot.severity === severity
    const matchesArea = area === 'All Bengaluru areas' || hotspot.zone === area
    return withinRange && matchesSeverity && matchesArea
  }).sort((a, b) => b.incidents - a.incidents), [dateRange, severity, area])

  return <div className="page-content accident-page">
    <div className="page-heading accident-page-heading"><div><div className="eyebrow page-eyebrow">CITY INTELLIGENCE <span className="heading-separator">/</span> ROAD SAFETY</div><h1>Accident Intelligence</h1><p>Explore illustrative collision patterns and hotspot signals across Bengaluru.</p></div><span className="demo-tag heading-demo"><span className="demo-dot" />DEMO DATA</span></div>
    <div className="accident-demo-banner"><span><CircleAlert size={15} /></span><div><strong>Illustrative demo data</strong><p>All counts, severity levels, map markers, and hotspot rankings on this page are sample values. Map points are not actual accident locations.</p></div></div>
    <div className="kpi-grid accident-kpi-grid">{demoAccidentSummary.map((metric) => <MetricCard key={metric.title} metric={metric} />)}</div>
    <div className="accident-filterbar panel"><div className="filterbar-title"><span><Filter size={15} /></span><div><strong>Filters</strong><small>Refine sample view</small></div></div><label className="accident-filter"><span>Date range</span><select value={dateRange} onChange={(event) => setDateRange(event.target.value)}><option value="7">Last 7 days</option><option value="30">Last 30 days</option><option value="90">Last 90 days</option></select><ChevronDown size={13} /></label><label className="accident-filter"><span>Severity</span><select value={severity} onChange={(event) => setSeverity(event.target.value)}><option>All severities</option><option>Critical</option><option>High</option><option>Moderate</option><option>Low</option></select><ChevronDown size={13} /></label><label className="accident-filter area-filter"><span>Bengaluru area</span><select value={area} onChange={(event) => setArea(event.target.value)}>{areaOptions.map((option) => <option key={option}>{option}</option>)}</select><ChevronDown size={13} /></label><span className="filter-demo"><span className="demo-dot" />Filters apply to DEMO DATA</span></div>
    <div className="accident-content-grid"><AccidentMap hotspots={filteredHotspots} /><AccidentTrend days={dateRange} /></div>
    <HotspotTable hotspots={filteredHotspots} />
    <div className="accident-page-foot"><span><Crosshair size={13} /> Sample geographic visualization · OpenStreetMap</span><span>DEMO DATA · NOT FOR OPERATIONAL USE</span></div>
  </div>
}
