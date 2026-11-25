import { useEffect, useMemo, useRef, useState } from 'react'
import { MapContainer, Marker, Popup, TileLayer, Tooltip as MapTooltip, ZoomControl } from 'react-leaflet'
import L from 'leaflet'
import {
  Activity, AlertTriangle, ArrowDownToLine, BellRing, CarFront, Check,
  ChevronDown, CircleAlert, Clock3, Construction, Gauge, MapPin, Pause,
  Play, Radio, RotateCcw, ShieldAlert, TrafficCone, Zap,
} from 'lucide-react'
import {
  Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import {
  liveEventAreas,
  liveEventCategories, liveEventSeverities,
} from '../../data/demoLiveEvents.js'
import { getLiveEvents, postNextLiveEvent } from '../../services/api.js'

const eventIcons = {
  Accident: CarFront,
  Speeding: Gauge,
  'Traffic congestion': TrafficCone,
  'Signal violation': ShieldAlert,
  'Road blockage': Construction,
}
const severityClass = { Low: 'low', Medium: 'medium', High: 'high', Critical: 'critical' }
const numberFormat = new Intl.NumberFormat('en-IN')
const tooltipStyle = { background: '#142333', border: '1px solid #2b4354', borderRadius: 8, color: '#edf4fa', fontSize: 10 }

function DemoTag({ children = 'SIMULATED' }) {
  return <span className="demo-tag"><span className="demo-dot" />{children}</span>
}

function timeLabel(timestamp) {
  return new Intl.DateTimeFormat('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }).format(new Date(timestamp))
}

function dateTimeLabel(timestamp) {
  return new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }).format(new Date(timestamp))
}

function FilterSelect({ label, value, onChange, options }) {
  return <label className="live-filter"><span>{label}</span><select value={value} onChange={(event) => onChange(event.target.value)}>{options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select><ChevronDown size={13} /></label>
}

function LiveMetric({ icon: Icon, tone, label, value, helper, live = false }) {
  return <article className="panel live-metric-card"><div className="live-metric-top"><span className={`kpi-icon icon-${tone}`}><Icon size={18} /></span><DemoTag /></div><div className="live-metric-label">{label}</div><div className="live-metric-value">{numberFormat.format(value)}</div><div className="live-metric-helper">{live && <span className="live-indicator" />}{helper}</div></article>
}

function createEventMarkerIcon(severity, selected) {
  return L.divIcon({
    className: 'live-marker-shell',
    html: `<span class="live-event-marker live-severity-${severityClass[severity] || 'medium'} ${selected ? 'live-marker-selected' : ''}"><i></i></span>`,
    iconSize: [25, 25],
    iconAnchor: [12, 12],
  })
}

function EventMap({ events, selectedId, onSelect }) {
  return <section className="panel live-map-card"><div className="live-section-heading"><div><div className="eyebrow">CITY EVENT MAP <DemoTag /></div><h2>Simulated event locations</h2><p>Markers use illustrative coordinates for Bengaluru areas.</p></div><span className="live-map-icon"><MapPin size={15} /></span></div>
    <div className="live-map-frame"><MapContainer center={[12.9716, 77.5946]} zoom={11} zoomControl={false} dragging={true} scrollWheelZoom className="live-map" aria-label="Map of Bengaluru showing simulated event locations"><TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" /><ZoomControl position="bottomright" />
      {events.map((event) => <Marker key={event.id} position={[event.coordinates.lat, event.coordinates.lng]} icon={createEventMarkerIcon(event.severity, event.id === selectedId)} eventHandlers={{ click: () => onSelect(event) }}><MapTooltip direction="top" offset={[0, -9]}>{event.eventType} · {event.location}</MapTooltip><Popup><div className="live-map-popup"><strong>{event.eventType}</strong><span>{event.location} · {event.severity}</span><button type="button" onClick={() => onSelect(event)}>View event details</button></div></Popup></Marker>)}
    </MapContainer><div className="live-map-notice"><CircleAlert size={13} /><span><strong>SIMULATED LOCATIONS</strong> · These markers are demo coordinates, not live incident locations.</span></div><div className="live-map-legend"><span className="legend-critical" />Critical<span className="legend-high" />High<span className="legend-medium" />Medium<span className="legend-low" />Low</div><div className="live-map-count"><MapPin size={12} />{events.length} filtered</div></div>
  </section>
}

function EventActivityChart({ events }) {
  const data = useMemo(() => {
    const latestEventTime = events.reduce((latest, event) => Math.max(latest, new Date(event.timestamp).getTime()), 0)
    const buckets = Array.from({ length: 7 }, (_, index) => ({ label: index === 6 ? 'Now' : `${(6 - index) * 10}m`, events: 0 }))
    events.forEach((event) => {
      const minutesAgo = Math.max(0, (latestEventTime - new Date(event.timestamp).getTime()) / 60000)
      const bucketIndex = Math.max(0, 6 - Math.min(6, Math.floor(minutesAgo / 10)))
      buckets[bucketIndex].events += 1
    })
    return buckets
  }, [events])

  return <section className="panel live-activity-card"><div className="live-section-heading"><div><div className="eyebrow">STREAM ACTIVITY <DemoTag /></div><h2>Recent event volume</h2><p>Filtered event count over the last hour</p></div><span className="activity-window"><Activity size={13} />60 MIN</span></div>
    {events.length ? <div className="live-activity-chart"><ResponsiveContainer width="100%" height="100%"><AreaChart data={data} margin={{ top: 10, right: 8, left: -20, bottom: 0 }}><defs><linearGradient id="liveActivityFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#3bcfc2" stopOpacity={0.25} /><stop offset="100%" stopColor="#3bcfc2" stopOpacity={0.01} /></linearGradient></defs><CartesianGrid stroke="#1c2b3d" strokeDasharray="3 5" vertical={false} /><XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fill: '#718398', fontSize: 9 }} dy={7} /><YAxis allowDecimals={false} axisLine={false} tickLine={false} tick={{ fill: '#718398', fontSize: 9 }} /><Tooltip contentStyle={tooltipStyle} formatter={(value) => [value, 'SIMULATED EVENTS']} /><Area type="monotone" dataKey="events" stroke="#3bcfc2" strokeWidth={2} fill="url(#liveActivityFill)" activeDot={{ r: 4, fill: '#3bcfc2' }} /></AreaChart></ResponsiveContainer></div> : <div className="live-chart-empty"><Activity size={17} /><span>No matching events to chart.</span></div>}
    <div className="live-chart-foot"><span>Rolling activity · simulated stream</span><span>SIMULATED</span></div>
  </section>
}

function EventFeed({ events, selectedId, onSelect, running, loading }) {
  return <section className="panel live-feed-card"><div className="live-section-heading"><div><div className="eyebrow">INCOMING EVENTS <DemoTag /></div><h2>Simulated event feed</h2><p>Newest events appear at the top.</p></div><span className={`feed-stream-state ${running ? 'feed-running' : 'feed-paused'}`}><i />{loading ? 'LOADING' : running ? 'GENERATING' : 'PAUSED'}</span></div>
    <div className="live-feed-head"><span>EVENT / TYPE</span><span>LOCATION</span><span>SEVERITY</span><span>TIME</span><span>STATUS</span></div>
    {loading ? <div className="live-feed-empty"><Radio size={20} /><strong>Loading simulated events</strong><span>Fetching the current event list from the backend.</span></div> : events.length ? <div className="live-feed-list">{events.map((event) => { const Icon = eventIcons[event.eventType] || Activity; return <button type="button" className={`live-feed-row ${selectedId === event.id ? 'live-feed-row-selected' : ''}`} key={event.id} onClick={() => onSelect(event)} title={`View details for ${event.id}`}><span className="feed-type-cell"><span className={`feed-event-icon live-severity-${severityClass[event.severity]}`}><Icon size={15} /></span><span><strong>{event.id}</strong><small>{event.eventType}</small></span></span><span className="feed-location"><MapPin size={12} />{event.location}</span><span><i className={`live-severity-pill live-severity-${severityClass[event.severity]}`}><b />{event.severity}</i></span><time dateTime={event.timestamp}>{timeLabel(event.timestamp)}</time><span><i className={`event-status event-status-${event.status.toLowerCase()}`}>{event.status}</i></span></button> })}</div> : <div className="live-feed-empty"><Radio size={20} /><strong>No events match these filters</strong><span>Change a filter to see the simulated feed.</span></div>}
    <div className="live-feed-footer"><span><span className={running ? 'status-dot' : 'status-dot status-dot-muted'} />{running ? 'Simulated stream is active' : 'Stream paused'}</span><span>{events.length} displayed · maximum 60</span></div>
  </section>
}

function EventDetails({ event }) {
  if (!event) return <section className="panel event-details-card"><div className="live-section-heading"><div><div className="eyebrow">EVENT INSPECTOR <DemoTag /></div><h2>Event details</h2></div><span className="details-icon"><ArrowDownToLine size={14} /></span></div><div className="event-details-empty"><span><BellRing size={18} /></span><strong>Select an event to inspect it</strong><p>Choose a feed row or map marker to view the simulated event payload.</p></div></section>

  const Icon = eventIcons[event.eventType] || Activity
  return <section className="panel event-details-card"><div className="live-section-heading"><div><div className="eyebrow">EVENT INSPECTOR <DemoTag /></div><h2>Event details</h2></div><span className="details-icon"><Check size={14} /></span></div><div className="selected-event-summary"><span className={`feed-event-icon live-severity-${severityClass[event.severity]}`}><Icon size={17} /></span><div><strong>{event.eventType}</strong><span>{event.id}</span></div><i className={`live-severity-pill live-severity-${severityClass[event.severity]}`}><b />{event.severity}</i></div><div className="selected-event-meta"><span><MapPin size={13} />Location</span><strong>{event.location}</strong><span><Clock3 size={13} />Timestamp</span><strong>{dateTimeLabel(event.timestamp)}</strong><span><Activity size={13} />Event status</span><strong><i className={`event-status event-status-${event.status.toLowerCase()}`}>{event.status}</i></strong></div><div className="payload-label"><span>SIMULATED JSON PAYLOAD</span><DemoTag /></div><pre className="event-payload">{JSON.stringify(event, null, 2)}</pre></section>
}

export default function LiveMonitoring() {
  const [events, setEvents] = useState([])
  const [isRunning, setIsRunning] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [hasLoadedEvents, setHasLoadedEvents] = useState(false)
  const [error, setError] = useState('')
  const [sessionReceived, setSessionReceived] = useState(0)
  const [selectedId, setSelectedId] = useState(null)
  const [categoryFilter, setCategoryFilter] = useState('All event categories')
  const [severityFilter, setSeverityFilter] = useState('All severities')
  const [areaFilter, setAreaFilter] = useState('All Bengaluru areas')
  const mountedRef = useRef(false)
  const postRequestRef = useRef(null)

  useEffect(() => {
    let active = true
    mountedRef.current = true

    async function loadInitialEvents() {
      try {
        const response = await getLiveEvents()
        if (response.status !== 'success' || !Array.isArray(response.data)) {
          throw new Error('The live events API returned an unexpected response.')
        }

        if (active) {
          setEvents(response.data)
          setHasLoadedEvents(true)
          setIsRunning(true)
          setError('')
        }
      } catch (requestError) {
        if (active) {
          setError(
            requestError.response?.data?.detail ||
            requestError.message ||
            'Unable to load simulated events from the backend.'
          )
          setIsRunning(false)
        }
      } finally {
        if (active) setIsLoading(false)
      }
    }

    loadInitialEvents()

    return () => {
      active = false
      mountedRef.current = false
    }
  }, [])

  useEffect(() => {
    if (!isRunning || isLoading || isRefreshing || !hasLoadedEvents) {
      return undefined
    }

    const intervalId = window.setInterval(async () => {
      // Do not start a second POST while the previous request is pending.
      if (postRequestRef.current) return

      const request = postNextLiveEvent()
      postRequestRef.current = request

      try {
        const response = await request
        if (response.status !== 'success' || !response.data?.id) {
          throw new Error('The live events API returned an unexpected event.')
        }

        if (mountedRef.current) {
          setEvents((currentEvents) => [response.data, ...currentEvents].slice(0, 60))
          setSessionReceived((count) => count + 1)
          setError('')
        }
      } catch (requestError) {
        if (mountedRef.current) {
          setError(
            requestError.response?.data?.detail ||
            requestError.message ||
            'Unable to request the next simulated event.'
          )
        }
      } finally {
        if (postRequestRef.current === request) {
          postRequestRef.current = null
        }
      }
    }, 4500)
    return () => window.clearInterval(intervalId)
  }, [isRunning, isLoading, isRefreshing, hasLoadedEvents])

  const visibleEvents = useMemo(() => events.filter((event) => (
    (categoryFilter === 'All event categories' || event.eventType === categoryFilter)
    && (severityFilter === 'All severities' || event.severity === severityFilter)
    && (areaFilter === 'All Bengaluru areas' || event.location === areaFilter)
  )), [events, categoryFilter, severityFilter, areaFilter])
  const selectedEvent = visibleEvents.find((event) => event.id === selectedId) || null
  const activeCount = events.filter((event) => event.status === 'Active').length
  const priorityCount = events.filter((event) => event.severity === 'High' || event.severity === 'Critical').length
  const streamActive = isRunning && hasLoadedEvents && !isLoading && !isRefreshing

  const refreshStream = async () => {
    const wasRunning = isRunning
    setIsRunning(false)
    setIsRefreshing(true)
    setSessionReceived(0)
    setSelectedId(null)
    setCategoryFilter('All event categories')
    setSeverityFilter('All severities')
    setAreaFilter('All Bengaluru areas')

    try {
      // Let any event already requested finish before loading the snapshot.
      if (postRequestRef.current) {
        await postRequestRef.current.catch(() => {})
      }
      if (!mountedRef.current) return

      const response = await getLiveEvents()
      if (response.status !== 'success' || !Array.isArray(response.data)) {
        throw new Error('The live events API returned an unexpected response.')
      }

      if (mountedRef.current) {
        setEvents(response.data)
        setHasLoadedEvents(true)
        setError('')
        setIsRunning(wasRunning)
      }
    } catch (requestError) {
      if (mountedRef.current) {
        setError(
          requestError.response?.data?.detail ||
          requestError.message ||
          'Unable to refresh simulated events from the backend.'
        )
        setIsRunning(wasRunning)
      }
    } finally {
      if (mountedRef.current) setIsRefreshing(false)
    }
  }

  return <div className="page-content live-page">
    <div className="page-heading live-page-heading"><div><div className="eyebrow page-eyebrow">CITY INTELLIGENCE <span className="heading-separator">/</span> EVENT STREAM</div><h1>Live Monitoring</h1><p>Monitor simulated traffic events and road-safety activity across Bengaluru.</p></div><DemoTag /></div>
    <div className="live-demo-notice"><span><CircleAlert size={15} /></span><div><strong>SIMULATED DATA · BACKEND-GENERATED</strong><p>Events are generated by the URBAN PULSE simulator, not real-time Bengaluru traffic systems. Map coordinates are illustrative.</p></div></div>
    {error && <div className="live-demo-notice" role="alert"><span><CircleAlert size={15} /></span><div><strong>SIMULATED EVENT REQUEST FAILED</strong><p>{error}</p></div></div>}
    <div className="live-summary-grid"><LiveMetric icon={Activity} tone="cyan" label="Total incoming events" value={events.length} helper="In current feed · max 60" /><LiveMetric icon={AlertTriangle} tone="amber" label="Active incidents" value={activeCount} helper="Across current simulated events" /><LiveMetric icon={Zap} tone="blue" label="High-priority events" value={priorityCount} helper="High and critical simulated events" /><LiveMetric icon={Radio} tone="violet" label="Events received in session" value={sessionReceived} helper={streamActive ? 'New simulated events every 4.5 seconds' : 'Waiting while paused'} live={streamActive} /></div>
    <section className="panel stream-control-panel"><div className="stream-control-info"><span className={`stream-status-icon ${streamActive ? 'stream-status-running' : 'stream-status-paused'}`}>{streamActive ? <Radio size={17} /> : <Pause size={17} />}</span><div><div><strong>Simulated event stream</strong><span className={`stream-status-pill ${streamActive ? 'is-running' : 'is-paused'}`}><i />{isLoading ? 'LOADING' : isRefreshing ? 'REFRESHING' : streamActive ? 'GENERATING' : 'PAUSED'}</span></div><p>{isLoading ? 'Loading simulated events from the backend.' : streamActive ? 'Requesting generated simulated events every 4.5 seconds.' : 'Generation is paused. Existing backend events remain available.'}</p></div></div><div className="stream-buttons"><button type="button" className="stream-button stream-start" onClick={() => setIsRunning(true)} disabled={isRunning || isLoading || isRefreshing || !hasLoadedEvents}><Play size={14} fill="currentColor" />Start stream</button><button type="button" className="stream-button stream-pause" onClick={() => setIsRunning(false)} disabled={!isRunning || isRefreshing}><Pause size={14} />Pause stream</button><button type="button" className="stream-button stream-reset" onClick={refreshStream} disabled={isRefreshing || isLoading}><RotateCcw size={14} />{isRefreshing ? 'Refreshing...' : 'Refresh simulated feed'}</button></div></section>
    <section className="panel live-filters"><div className="live-filter-title"><span><Activity size={15} /></span><div><strong>Event filters</strong><small>Apply to feed, map and activity</small></div></div><FilterSelect label="Event category" value={categoryFilter} onChange={setCategoryFilter} options={[{ value: 'All event categories', label: 'All categories' }, ...liveEventCategories.map((category) => ({ value: category, label: category }))]} /><FilterSelect label="Severity" value={severityFilter} onChange={setSeverityFilter} options={[{ value: 'All severities', label: 'All severities' }, ...liveEventSeverities.map((severity) => ({ value: severity, label: severity }))]} /><FilterSelect label="Bengaluru area" value={areaFilter} onChange={setAreaFilter} options={[{ value: 'All Bengaluru areas', label: 'All areas' }, ...liveEventAreas.map((area) => ({ value: area.name, label: area.name }))]} /><span className="live-filter-demo"><span className="demo-dot" />Filtered simulated events</span></section>
    <div className="live-workspace-grid"><div className="live-workspace-main"><EventFeed events={visibleEvents} selectedId={selectedId} onSelect={(event) => setSelectedId(event.id)} running={streamActive} loading={isLoading && !hasLoadedEvents} /><EventActivityChart events={visibleEvents} /></div><div className="live-workspace-side"><EventMap events={visibleEvents} selectedId={selectedId} onSelect={(event) => setSelectedId(event.id)} /><EventDetails event={selectedEvent} /></div></div>
    <div className="live-page-footer"><span><Activity size={13} />Backend-generated simulated events · not real-time traffic.</span><span>NOT LIVE TRAFFIC DATA</span></div>
  </div>
}
