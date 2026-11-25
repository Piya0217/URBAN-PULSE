
import { useEffect, useMemo, useState } from 'react'
import {
  Activity,
  AlertOctagon,
  ArrowDownRight,
  ArrowUpRight,
  CarFront,
  CircleAlert,
  Filter,
  MapPin,
  ShieldAlert,
  Target,
} from 'lucide-react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  getYearlyAccidents,
  getAccidentZones,
  getAccidentStations,
  getAccidentHotspots,
  getAccidentTrends,
} from '../../services/api.js'

const YEARS = ['2023', '2024', '2025']
const ZONES = ['All zones', 'East', 'West', 'North', 'South']

const numberFormat = new Intl.NumberFormat('en-IN')

const formatNumber = (value) => {
  if (value === null || value === undefined || value === '') return '—'

  const numericValue = Number(value)
  return Number.isFinite(numericValue)
    ? numberFormat.format(numericValue)
    : '—'
}

const formatPercentage = (value) => {
  if (value === null || value === undefined || value === '') return '—'

  const numericValue = Number(value)
  return Number.isFinite(numericValue)
    ? `${numericValue.toFixed(2)}%`
    : '—'
}

function MetricCard({ title, value, note, icon: Icon, tone }) {
  return (
    <article className="kpi-card panel accident-kpi">
      <div className="kpi-card-top">
        <span className={`kpi-icon icon-${tone}`}>
          <Icon size={18} />
        </span>
        <span className="historical-tag">HISTORICAL DATA</span>
      </div>
      <div className="kpi-title">{title}</div>
      <div className="kpi-value">{value}</div>
      <div className="kpi-footer">
        <span className="kpi-note">{note}</span>
      </div>
    </article>
  )
}

function AccidentTrend({ data }) {
  return (
    <section className="panel accident-trend-card">
      <div className="panel-heading">
        <div>
          <div className="eyebrow">INCIDENT HISTORY</div>
          <h2>Annual accident trend</h2>
          <p>Recorded crashes from 2023 to 2025</p>
        </div>
        <span className="trend-period">
          <Activity size={13} />
          3 years
        </span>
      </div>

      <div className="trend-chart">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{ top: 10, right: 5, left: -22, bottom: 0 }}
          >
            <defs>
              <linearGradient
                id="accidentTrendFill"
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop offset="0%" stopColor="#f0aa54" stopOpacity={0.25} />
                <stop offset="100%" stopColor="#f0aa54" stopOpacity={0.01} />
              </linearGradient>
            </defs>

            <CartesianGrid
              stroke="#1c2b3d"
              strokeDasharray="3 5"
              vertical={false}
            />
            <XAxis
              dataKey="year"
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#697c92', fontSize: 10 }}
              dy={8}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#697c92', fontSize: 10 }}
            />
            <Tooltip
              contentStyle={{
                background: '#142333',
                border: '1px solid #2b4354',
                borderRadius: 8,
                color: '#edf4fa',
                fontSize: 11,
              }}
              formatter={(value) => [
                `${formatNumber(value)} crashes`,
                'Recorded crashes',
              ]}
            />
            <Area
              type="monotone"
              dataKey="total_crashes"
              name="Recorded crashes"
              stroke="#f0ae59"
              strokeWidth={2}
              fill="url(#accidentTrendFill)"
              activeDot={{
                r: 4,
                fill: '#f0ae59',
                stroke: '#0d1826',
                strokeWidth: 2,
              }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="trend-footer">
        <span>Annual crash records</span>
        <span>Source: Bengaluru crash dataset</span>
      </div>
    </section>
  )
}

function ZoneAnalytics({ zones }) {
  return (
    <section className="panel accident-zone-card">
      <div className="panel-heading">
        <div>
          <div className="eyebrow">ZONE ANALYTICS</div>
          <h2>Accidents by zone</h2>
          <p>Recorded crashes across Bengaluru zones</p>
        </div>
        <span className="zone-wise-tag">
          <MapPin size={14} />
          Zone-wise
        </span>
      </div>

      {zones.length ? (
        <>
          <div className="zone-chart">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={zones}
                layout="vertical"
                margin={{ top: 5, right: 18, left: 0, bottom: 5 }}
                barCategoryGap="28%"
              >
                <CartesianGrid
                  stroke="#1c2b3d"
                  strokeDasharray="3 5"
                  horizontal={false}
                />

                <XAxis
                  type="number"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#71869a', fontSize: 10 }}
                />

                <YAxis
                  type="category"
                  dataKey="zone"
                  axisLine={false}
                  tickLine={false}
                  width={55}
                  tick={{ fill: '#b5c5d3', fontSize: 11 }}
                />

                <Tooltip
                  cursor={{ fill: '#ffffff08' }}
                  contentStyle={{
                    background: '#142333',
                    border: '1px solid #2b4354',
                    borderRadius: 8,
                    color: '#edf4fa',
                    fontSize: 11,
                  }}
                  formatter={(value, name) => [
                    formatNumber(value),
                    name === 'fatal_crashes' ? 'Fatal crashes' : 'Non-fatal crashes',
                  ]}
                />

                <Legend
                  verticalAlign="bottom"
                  align="left"
                  iconType="circle"
                  iconSize={8}
                  wrapperStyle={{
                    fontSize: '10px',
                    color: '#91a4b7',
                    paddingTop: '12px',
                  }}
                  formatter={(value) =>
                    value === 'fatal_crashes' ? 'Fatal' : 'Non-fatal'
                  }
                />

                <Bar
                  dataKey="fatal_crashes"
                  stackId="crashes"
                  fill="#e5a34f"
                  radius={[3, 0, 0, 3]}
                  barSize={19}
                />

                <Bar
                  dataKey="non_fatal_crashes"
                  stackId="crashes"
                  fill="#36bdb5"
                  radius={[0, 3, 3, 0]}
                  barSize={19}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="zone-total-list">
            {zones.map((item) => (
              <div className="zone-total-row" key={item.zone}>
                <span>{item.zone}</span>
                <strong>{formatNumber(item.total_crashes)} crashes</strong>
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="accident-empty">
          No zone records for these filters.
        </div>
      )}

      <div className="zone-footnote">
        <CircleAlert size={13} />
        Based on recorded historical crash counts
      </div>
    </section>
  )
}

function HotspotTable({ hotspots }) {
  return (
    <section className="panel hotspot-table-card">
      <div className="panel-heading hotspot-table-heading">
        <div>
          <div className="eyebrow">PRIORITY AREAS</div>
          <h2>Historical hotspot ranking</h2>
          <p>Stations ranked by their combined 2023–2025 crash counts</p>
        </div>
        <span className="zone-wise-tag">
          <Target size={14} />
          Top locations
        </span>
      </div>

      <div className="hotspot-table-scroll">
        <table className="hotspot-table">
          <thead>
            <tr>
              <th>RANK / STATION</th>
              <th>ZONE</th>
              <th>3-YEAR CRASHES</th>
              <th>FATAL</th>
              <th>FATAL %</th>
            </tr>
          </thead>
          <tbody>
            {hotspots.length ? (
              hotspots.map((hotspot, index) => (
                <tr key={hotspot.station}>
                  <td>
                    <span className="rank-number">
                      {String(index + 1).padStart(2, '0')}
                    </span>
                    <span className="table-area">
                      <strong>{hotspot.station}</strong>
                      <small>
                        <MapPin size={11} />
                        Historical station record
                      </small>
                    </span>
                  </td>
                  <td className="table-zone">{hotspot.zone}</td>
                  <td>
                    <strong className="incident-count">
                      {formatNumber(hotspot.three_year_crashes)}
                    </strong>
                  </td>
                  <td>{formatNumber(hotspot.three_year_fatal_crashes)}</td>
                  <td>{formatPercentage(hotspot.fatal_crash_percentage)}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="5" className="empty-hotspots">
                  No historical hotspots match this zone.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="table-footnote">
        <span>
          <CircleAlert size={13} />
          Three-year historical counts; not a prediction of future accidents.
        </span>
        <span>Showing {hotspots.length} stations</span>
      </div>
    </section>
  )
}

function StationTrends({ trends, stationRecordCount })  {
  return (
    <section className="panel station-trends-card">
      <div className="panel-heading">
        <div>
          <div className="eyebrow">YEAR-OVER-YEAR COMPARISON</div>
          <h2>Station crash trends</h2>
          <p>
  Change in recorded crashes between 2023 and 2025 · {stationRecordCount} annual station records
</p>
        </div>
      </div>

      <div className="hotspot-table-scroll">
        <table className="hotspot-table station-trends-table">
          <thead>
            <tr>
              <th>STATION</th>
              <th>ZONE</th>
              <th>2023</th>
              <th>2024</th>
              <th>2025</th>
              <th>CHANGE (%)</th>
            </tr>
          </thead>
          <tbody>
            {trends.length ? (
              trends.map((station) => {
                const changeValue = station.percentage_change
                const change =
                  changeValue === null || changeValue === undefined || changeValue === ''
                    ? null
                    : Number(changeValue)
                const hasValidChange = Number.isFinite(change)
                const isIncrease = hasValidChange && change > 0

                return (
                  <tr key={station.station}>
                    <td>
                      <span className="station-trend-name">
                        {station.station}
                      </span>
                    </td>
                    <td className="table-zone">{station.zone}</td>
                    <td>{formatNumber(station['2023'])}</td>
                    <td>{formatNumber(station['2024'])}</td>
                    <td>{formatNumber(station['2025'])}</td>
                    <td>
                      <span
                        className={`station-change ${
                          isIncrease
                            ? 'increase'
                            : hasValidChange && change < 0
                              ? 'decrease'
                              : 'unchanged'
                        }`}
                      >
                        {isIncrease ? (
                          <ArrowUpRight size={13} />
                        ) : change < 0 ? (
                          <ArrowDownRight size={13} />
                        ) : null}
                        {isIncrease ? '+' : ''}
                        {formatPercentage(changeValue)}
                      </span>
                    </td>
                  </tr>
                )
              })
            ) : (
              <tr>
                <td colSpan="6" className="empty-hotspots">
                  No station trends match this zone.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default function AccidentIntelligence() {
  const [year, setYear] = useState('2025')
  const [zone, setZone] = useState('All zones')

  const [yearly, setYearly] = useState([])
  const [zoneRecords, setZoneRecords] = useState([])
  const [stationRecordCount, setStationRecordCount] = useState(0)
  const [hotspotRecords, setHotspotRecords] = useState([])
  const [trendRecords, setTrendRecords] = useState([])

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    async function loadAccidentData() {
      try {
        setLoading(true)
        setError('')

        const [
          yearlyResponse,
          zonesResponse,
          stationsResponse,
          hotspotsResponse,
          trendsResponse,
        ] = await Promise.all([
          getYearlyAccidents(),
          getAccidentZones(),
          getAccidentStations(),
          getAccidentHotspots(),
          getAccidentTrends(),
        ])

        if (!active) return

        setYearly(
          [...(yearlyResponse.data || [])].sort(
            (a, b) => Number(a.year) - Number(b.year)
          )
        )
        setZoneRecords(zonesResponse.data || [])
        setStationRecordCount(
          stationsResponse.count ?? stationsResponse.data?.length ?? 0
        )
        setHotspotRecords(hotspotsResponse.data || [])
        setTrendRecords(trendsResponse.data || [])
      } catch (err) {
        if (!active) return

        console.error('Failed to load accident analytics:', err)
        setError(
          err.response?.data?.detail ||
          'Unable to load accident analytics. Check that the backend API is running.'
        )
      } finally {
        if (active) setLoading(false)
      }
    }

    loadAccidentData()

    return () => {
      active = false
    }
  }, [])

  const selectedYear = useMemo(
    () => yearly.find((record) => String(record.year) === year),
    [yearly, year]
  )

  const selectedZones = useMemo(
    () =>
      zoneRecords
        .filter(
          (record) =>
            String(record.year) === year &&
            (zone === 'All zones' || record.zone === zone)
        )
        .sort((a, b) => b.total_crashes - a.total_crashes),
    [zoneRecords, year, zone]
  )

  const filteredHotspots = useMemo(
    () =>
      hotspotRecords
        .filter((record) => zone === 'All zones' || record.zone === zone)
        .sort((a, b) => b.three_year_crashes - a.three_year_crashes),
    [hotspotRecords, zone]
  )

  const filteredTrends = useMemo(
    () =>
      trendRecords
        .filter((record) => zone === 'All zones' || record.zone === zone)
        .sort((a, b) => {
          if (a.percentage_change == null) {
            return b.percentage_change == null ? 0 : 1
          }
          if (b.percentage_change == null) return -1

          return Number(b.percentage_change) - Number(a.percentage_change)
        }),
    [trendRecords, zone]
  )

  const fatalShare =
    selectedYear?.total_crashes != null &&
    selectedYear.total_crashes !== 0 &&
    selectedYear.fatal_crashes != null
      ? (selectedYear.fatal_crashes / selectedYear.total_crashes) * 100
      : null

  const metrics = [
    {
      title: 'Total crashes',
      value: formatNumber(selectedYear?.total_crashes),
      note: `Recorded in ${year}`,
      icon: CarFront,
      tone: 'blue',
    },
    {
      title: 'Fatal crashes',
      value: formatNumber(selectedYear?.fatal_crashes),
      note: `Recorded in ${year}`,
      icon: AlertOctagon,
      tone: 'neutral',
    },
    {
      title: 'Non-fatal crashes',
      value: formatNumber(selectedYear?.non_fatal_crashes),
      note: `Recorded in ${year}`,
      icon: ShieldAlert,
      tone: 'neutral',
    },
    {
      title: 'Fatal crash share',
      value: formatPercentage(fatalShare),
      note: 'Fatal crashes as a share of total',
      icon: Target,
      tone: 'purple',
    },
  ]

  if (loading) {
    return (
      <div className="page-content accident-page">
        <div className="accident-loading panel">
          Loading historical accident analytics...
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page-content accident-page">
        <div className="accident-error panel">
          <CircleAlert size={18} />
          <div>
            <strong>Accident analytics unavailable</strong>
            <p>{error}</p>
            <button onClick={() => window.location.reload()}>
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="page-content accident-page">
      <div className="page-heading accident-page-heading">
        <div>
          <div className="eyebrow page-eyebrow">
            CITY INTELLIGENCE <span className="heading-separator">/</span> ROAD
            SAFETY
          </div>
          <h1>Accident Intelligence</h1>
          <p>Explore historical collision patterns across Bengaluru.</p>
        </div>
        <span className="historical-tag heading-historical">
          HISTORICAL DATA
        </span>
      </div>

      <div className="accident-demo-banner historical-banner">
        <span>
          <CircleAlert size={15} />
        </span>
        <div>
          <strong>Historical accident analytics</strong>
          <p>
            Figures are based on recorded Bengaluru crash data. Hotspot
            rankings represent combined 2023–2025 counts, not predictions or
            individual road-risk probabilities.
          </p>
        </div>
      </div>

      <div className="kpi-grid accident-kpi-grid">
        {metrics.map((metric) => (
          <MetricCard key={metric.title} {...metric} />
        ))}
      </div>

      <div className="accident-filterbar panel">
        <div className="filterbar-title">
          <span>
            <Filter size={15} />
          </span>
          <div>
            <strong>Filters</strong>
            <small>Refine historical data</small>
          </div>
        </div>

        <label className="accident-filter">
          <span>Year</span>
          <select value={year} onChange={(event) => setYear(event.target.value)}>
            {YEARS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>

        <label className="accident-filter area-filter">
          <span>Zone</span>
          <select value={zone} onChange={(event) => setZone(event.target.value)}>
            {ZONES.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>

        <span className="filter-demo historical-indicator">
          <span className="historical-dot" />
          Historical records
        </span>
      </div>

      <div className="accident-content-grid">
        <ZoneAnalytics zones={selectedZones} />
        <AccidentTrend data={yearly} />
      </div>

      <HotspotTable hotspots={filteredHotspots} />
      <StationTrends
  trends={filteredTrends}
  stationRecordCount={stationRecordCount}
/>

      <div className="accident-page-foot">
        <span>
          <Target size={13} />
          Historical station and zone analytics
        </span>
        <span>BASED ON RECORDED DATA · NOT A PREDICTION</span>
      </div>
    </div>
  )
}
