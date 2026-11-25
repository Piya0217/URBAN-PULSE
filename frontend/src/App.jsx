import { useState } from 'react'
import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom'
import {
  Activity, AlertTriangle, ArrowDownRight, ArrowUpRight, Bell, Bike,
  CarFront, ChevronDown, Clock3, Gauge, LayoutDashboard, MapPin,
  Menu, Radio, ShieldAlert, Sparkles, TrafficCone, X,
} from 'lucide-react'
import {
  Area, AreaChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from 'recharts'
import AccidentIntelligence from './components/accidents/AccidentIntelligence.jsx'
import ViolationAnalytics from './components/violations/ViolationAnalytics.jsx'
import PredictiveInsights from './components/insights/PredictiveInsights.jsx'
import LiveMonitoring from './components/live/LiveMonitoring.jsx'

const navigation = [
  { label: 'Overview', path: '/', icon: LayoutDashboard },
  { label: 'Accident Intelligence', path: '/accidents', icon: CarFront },
  { label: 'Violation Analytics', path: '/violations', icon: ShieldAlert },
  { label: 'Predictive Insights', path: '/insights', icon: Sparkles },
  { label: 'Live Monitoring', path: '/live', icon: Radio },
]

const accidentTrend = [
  { day: 'Mon', incidents: 32 }, { day: 'Tue', incidents: 45 },
  { day: 'Wed', incidents: 38 }, { day: 'Thu', incidents: 58 },
  { day: 'Fri', incidents: 49 }, { day: 'Sat', incidents: 68 },
  { day: 'Sun', incidents: 54 }, { day: 'Mon', incidents: 72 },
  { day: 'Tue', incidents: 61 }, { day: 'Wed', incidents: 82 },
  { day: 'Thu', incidents: 66 }, { day: 'Fri', incidents: 93 },
]

const violationMix = [
  { name: 'Speeding', value: 38, color: '#20c9c1' },
  { name: 'Signal jump', value: 26, color: '#4c89ff' },
  { name: 'No helmet', value: 21, color: '#f0ad54' },
  { name: 'Other', value: 15, color: '#7567df' },
]

const alerts = [
  { icon: AlertTriangle, color: 'amber', title: 'Collision detected', place: 'Outer Ring Road · Marathahalli', time: '2 min ago', tag: 'HIGH' },
  { icon: Bike, color: 'cyan', title: 'Helmet violation spike', place: 'Hosur Road · Silk Board', time: '14 min ago', tag: 'MEDIUM' },
  { icon: TrafficCone, color: 'blue', title: 'Traffic flow disruption', place: 'Whitefield Main Road', time: '32 min ago', tag: 'LOW' },
]

function DemoTag({ children = 'DEMO DATA' }) {
  return <span className="demo-tag"><span className="demo-dot" />{children}</span>
}

function Sidebar({ open, onClose }) {
  return (
    <>
      {open && <button aria-label="Close navigation overlay" className="sidebar-overlay" onClick={onClose} />}
      <aside className={`sidebar ${open ? 'sidebar-open' : ''}`}>
        <div className="brand-lockup">
          <div className="brand-mark"><Activity size={20} strokeWidth={2.4} /></div>
          <div><div className="brand-name">URBAN<span>PULSE</span></div><div className="brand-caption">MOBILITY INTELLIGENCE</div></div>
          <button className="icon-button sidebar-close" aria-label="Close navigation" onClick={onClose}><X size={18} /></button>
        </div>
        <div className="nav-section-label">WORKSPACE</div>
        <nav className="nav-list" aria-label="Main navigation">
          {navigation.map(({ label, path, icon: Icon }) => (
            <NavLink key={path} to={path} end={path === '/'} onClick={onClose} className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`}>
              <Icon size={18} strokeWidth={1.8} /><span>{label}</span>{label === 'Live Monitoring' && <span className="live-indicator" />}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="coverage-card">
            <div className="coverage-top"><span className="coverage-icon"><MapPin size={15} /></span><span>Coverage area</span></div>
            <div className="coverage-name">Bengaluru Urban</div>
            <div className="coverage-meta">8 zones <span>·</span> DEMO DATA</div>
            <div className="coverage-progress"><span /></div>
          </div>
          <div className="profile-row"><div className="avatar">UP</div><div className="profile-copy"><strong>Urban Pulse</strong><span>City operations</span></div><button className="icon-button profile-menu" aria-label="Profile menu"><ChevronDown size={16} /></button></div>
        </div>
      </aside>
    </>
  )
}

function Topbar({ onMenu }) {
  return <header className="topbar">
    <button className="icon-button mobile-menu" aria-label="Open navigation" onClick={onMenu}><Menu size={20} /></button>
    <div className="topbar-project"><span className="topbar-project-name">Urban Mobility Platform</span><span className="topbar-divider" /><span className="location-label"><MapPin size={14} /> Bengaluru, India <ChevronDown size={13} /></span></div>
    <div className="topbar-actions"><span className="system-status"><span className="status-dot" /> All systems operational</span><button className="icon-button notification-button" aria-label="Notifications"><Bell size={18} /><i /></button><div className="topbar-avatar">UP</div></div>
  </header>
}

function KpiCard({ title, value, unit, change, direction, icon: Icon, tone, note }) {
  return <article className="kpi-card panel">
    <div className="kpi-card-top"><span className={`kpi-icon icon-${tone}`}><Icon size={18} /></span><DemoTag /><button className="icon-button more-button" aria-label={`${title} options`}>···</button></div>
    <div className="kpi-title">{title}</div>
    <div className="kpi-value">{value}<span>{unit}</span></div>
    <div className="kpi-footer"><span className={`change-pill ${direction}`}><span>{direction === 'up' ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}{change}</span></span><span className="kpi-note">{note}</span></div>
  </article>
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return <div className="chart-tooltip"><span>{label}</span><strong>{payload[0].value} <small>incidents</small></strong></div>
}

function AccidentChart() {
  return <section className="panel chart-card accident-card">
    <div className="panel-heading"><div><div className="eyebrow">ROAD SAFETY <DemoTag /></div><h2>Accident trends</h2><p>Incident volume across the last 12 weeks</p></div><button className="period-button">Last 12 weeks <ChevronDown size={14} /></button></div>
    <div className="chart-legend"><span><i className="legend-dot teal-dot" />Reported incidents</span><span className="legend-demo">Illustrative trend · DEMO DATA</span></div>
    <div className="area-chart-wrap"><ResponsiveContainer width="100%" height="100%"><AreaChart data={accidentTrend} margin={{ top: 12, right: 8, left: -20, bottom: 0 }}>
      <defs><linearGradient id="incidentFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#19c9c0" stopOpacity={0.24} /><stop offset="100%" stopColor="#19c9c0" stopOpacity={0} /></linearGradient></defs>
      <CartesianGrid stroke="#1c2b3d" strokeDasharray="3 5" vertical={false} />
      <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: '#697c92', fontSize: 11 }} dy={10} />
      <YAxis axisLine={false} tickLine={false} tick={{ fill: '#697c92', fontSize: 11 }} ticks={[0, 25, 50, 75, 100]} />
      <Tooltip content={<ChartTooltip />} cursor={{ stroke: '#526a7b', strokeDasharray: '4 4' }} />
      <Area type="monotone" dataKey="incidents" stroke="#27d1c5" strokeWidth={2.5} fill="url(#incidentFill)" activeDot={{ r: 5, fill: '#27d1c5', stroke: '#0d1826', strokeWidth: 3 }} />
    </AreaChart></ResponsiveContainer></div>
    <div className="chart-footnote"><span><Clock3 size={13} />Updated 8 minutes ago</span><span>Source: sample dataset</span></div>
  </section>
}

function ViolationChart() {
  return <section className="panel chart-card violation-card">
    <div className="panel-heading"><div><div className="eyebrow">TRAFFIC ENFORCEMENT <DemoTag /></div><h2>Violation categories</h2><p>Distribution by violation type</p></div><button className="icon-button more-button" aria-label="Violation chart options">···</button></div>
    <div className="donut-content"><div className="donut-wrap"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={violationMix} dataKey="value" nameKey="name" innerRadius="70%" outerRadius="92%" paddingAngle={4} stroke="none" cornerRadius={5}>{violationMix.map((item) => <Cell key={item.name} fill={item.color} />)}</Pie><Tooltip formatter={(value) => [`${value}%`, 'DEMO DATA']} contentStyle={{ background: '#111f2f', border: '1px solid #26394c', borderRadius: 10, color: '#edf4fa', fontSize: 12 }} /></PieChart></ResponsiveContainer><div className="donut-center"><strong>100<span>%</span></strong><span>DEMO DATA</span></div></div><div className="donut-legend">{violationMix.map((item) => <div className="donut-legend-row" key={item.name}><span><i style={{ background: item.color }} />{item.name}</span><strong>{item.value}%</strong></div>)}</div></div>
    <div className="chart-footnote"><span>Sample category mix</span><span>DEMO DATA</span></div>
  </section>
}

function AlertsPanel() {
  return <section className="panel alerts-card">
    <div className="panel-heading alerts-heading"><div><div className="eyebrow">CITY SIGNALS <DemoTag /></div><h2>Recent alerts</h2></div><button className="text-link">View all <ArrowUpRight size={14} /></button></div>
    <div className="alerts-list">{alerts.map(({ icon: Icon, color, title, place, time, tag }) => <article className="alert-row" key={title}>
      <span className={`alert-icon alert-${color}`}><Icon size={17} /></span><div className="alert-copy"><div className="alert-title">{title} <span className={`severity severity-${tag.toLowerCase()}`}>{tag}</span></div><div className="alert-place"><MapPin size={12} />{place}</div></div><span className="alert-time">{time}</span>
    </article>)}</div>
    <div className="alerts-footer"><span className="status-dot" />Monitoring active <span className="footer-demo">All alerts are illustrative · DEMO DATA</span></div>
  </section>
}

function DataStatus() {
  return <section className="data-status panel"><div className="data-status-main"><span className="data-status-icon"><Activity size={17} /></span><div><strong>Data pipeline status</strong><span>Connected to sample data sources</span></div><DemoTag /></div><div className="source-status"><span className="status-dot" />Traffic sensors <strong>Demo</strong></div><div className="source-status"><span className="status-dot" />Incident feed <strong>Demo</strong></div><div className="source-status"><span className="status-dot" />Weather data <strong>Demo</strong></div><span className="data-updated">Updated just now</span></section>
}

function Overview() {
  return <div className="page-content">
    <div className="page-heading"><div><div className="eyebrow page-eyebrow">TUESDAY, NOVEMBER 25, 2026 <span className="heading-separator">/</span> CITY OVERVIEW</div><h1>Good morning, Bengaluru <span className="wave">✳</span></h1><p>Here’s what’s happening across your city today.</p></div><div className="heading-actions"><DemoTag /><button className="export-button"><Activity size={15} /> Live overview <span className="live-indicator" /></button></div></div>
    <div className="demo-banner"><span className="demo-banner-icon"><AlertTriangle size={15} /></span><span><strong>Demo environment</strong> — All metrics and visualizations below are illustrative sample data, not actual Bengaluru statistics.</span></div>
    <div className="kpi-grid">
      <KpiCard title="Reported incidents" value="1,284" unit="" change="12.8%" direction="up" note="vs. prior period" icon={CarFront} tone="cyan" />
      <KpiCard title="Traffic violations" value="8,642" unit="" change="6.4%" direction="down" note="vs. prior period" icon={ShieldAlert} tone="blue" />
      <KpiCard title="High-risk corridors" value="12" unit="" change="2 new" direction="up" note="identified this week" icon={Gauge} tone="amber" />
      <KpiCard title="Avg. response time" value="8.4" unit=" min" change="1.2 min" direction="down" note="faster than prior period" icon={Clock3} tone="violet" />
    </div>
    <div className="charts-grid"><AccidentChart /><ViolationChart /></div>
    <AlertsPanel />
    <DataStatus />
    <footer className="page-footer"><span>URBAN PULSE <span>·</span> MOBILITY INTELLIGENCE PLATFORM</span><span>DEMO DATA · NOT FOR OPERATIONAL USE</span></footer>
  </div>
}

function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const closeSidebar = () => setSidebarOpen(false)
  return <div className="app-shell"><Sidebar open={sidebarOpen} onClose={closeSidebar} /><main className="main-area"><Topbar onMenu={() => setSidebarOpen(true)} /><Routes><Route path="/" element={<Overview />} /><Route path="/accidents" element={<AccidentIntelligence />} /><Route path="/violations" element={<ViolationAnalytics />} /><Route path="/insights" element={<PredictiveInsights />} /><Route path="/live" element={<LiveMonitoring />} /></Routes></main></div>
}

export default function App() {
  return <BrowserRouter><AppShell /></BrowserRouter>
}
