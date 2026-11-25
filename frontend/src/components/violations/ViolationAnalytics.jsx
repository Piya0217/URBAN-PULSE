
import { useEffect, useMemo, useState } from 'react'
import {
  BarChart3,
  ChevronDown,
  CircleAlert,
  HardHat,
  RadioTower,
  ShieldAlert,
} from 'lucide-react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  demoViolationRecords,
  violationAreas,
  violationCategories,
} from '../../data/demoViolations.js'
import {
  getMotorVehicleYearly,
  getMotorVehicleTop10,
} from '../../services/api.js'

const tooltipStyle = {
  background: '#142333',
  border: '1px solid #2b4354',
  borderRadius: 8,
  color: '#edf4fa',
  fontSize: 10,
}

const numberFormat = new Intl.NumberFormat('en-IN')
const yearOptions = Array.from({ length: 8 }, (_, index) => 2018 + index)

function DemoTag() {
  return (
    <span className="demo-tag">
      <span className="demo-dot" />
      DEMO DATA
    </span>
  )
}

function HistoricalTag() {
  return <span className="demo-tag">HISTORICAL DATA</span>
}

function FilterSelect({ label, value, onChange, options }) {
  return (
    <label className="violation-filter">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <ChevronDown size={13} />
    </label>
  )
}

function MetricCard({ definition, value }) {
  const Icon = definition.icon

  return (
    <article className="kpi-card panel violation-kpi-card">
      <div className="kpi-card-top">
        <span className={`kpi-icon icon-${definition.tone}`}>
          <Icon size={18} />
        </span>
        <HistoricalTag />
      </div>
      <div className="kpi-title">{definition.title}</div>
      <div className="kpi-value">
        {value == null ? '—' : numberFormat.format(value)}
      </div>
      <div className="kpi-footer">
        <span className="change-pill down">
          <span>Recorded cases</span>
        </span>
        <span className="kpi-note">selected year</span>
      </div>
    </article>
  )
}

function ChartHeading({ eyebrow, title, subtitle, demo = false }) {
  return (
    <div className="panel-heading">
      <div>
        <div className="eyebrow">
          {eyebrow} {demo ? <DemoTag /> : <HistoricalTag />}
        </div>
        <h2>{title}</h2>
        <p>{subtitle}</p>
      </div>
    </div>
  )
}

function ChartEmpty() {
  return (
    <div className="violation-chart-empty">
      <CircleAlert size={18} />
      <strong>No matching records</strong>
      <span>Try changing the selected filters.</span>
    </div>
  )
}

function DistributionChart({ data, total }) {
  return (
    <section className="panel violation-chart-card distribution-card">
      <ChartHeading
        eyebrow="CATEGORY MIX"
        title="Violation distribution"
        subtitle="Top 10 recorded offences for the selected year"
      />

      {total ? (
        <div className="distribution-body">
          <div className="distribution-donut">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  dataKey="count"
                  nameKey="name"
                  innerRadius="66%"
                  outerRadius="91%"
                  paddingAngle={3}
                  cornerRadius={4}
                  stroke="none"
                >
                  {data.map((item) => (
                    <Cell key={item.name} fill={item.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={tooltipStyle}
                  formatter={(value, _name, item) => [
                    `${numberFormat.format(value)} (${item.payload.share}%)`,
                    'Recorded cases',
                  ]}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="distribution-center">
              <strong>{numberFormat.format(total)}</strong>
              <span>TOP 10 CASES</span>
            </div>
          </div>

          <div className="distribution-legend">
            {data.map((item) => (
              <div className="distribution-legend-item" key={item.name}>
                <span>
                  <i style={{ background: item.color }} />
                  {item.name}
                </span>
                <strong>{item.share}%</strong>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <ChartEmpty />
      )}

      <div className="violation-chart-footer">
        <span>Share calculated within the displayed top 10</span>
        <span>HISTORICAL DATA</span>
      </div>
    </section>
  )
}

function TrendChart({ data }) {
  return (
    <section className="panel violation-chart-card violation-trend-card">
      <ChartHeading
        eyebrow="ANNUAL ENFORCEMENT"
        title="Yearly violation trend"
        subtitle="Available recorded cases from 2018 to 2025"
      />

      {data.length ? (
        <div className="violation-line-chart">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={data}
              margin={{ top: 15, right: 10, left: -18, bottom: 0 }}
            >
              <CartesianGrid
                stroke="#1c2b3d"
                strokeDasharray="3 5"
                vertical={false}
              />
              <XAxis
                dataKey="year"
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#718398', fontSize: 9 }}
                dy={8}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#718398', fontSize: 9 }}
              />
              <Tooltip
                contentStyle={tooltipStyle}
                formatter={(value) => [
                  numberFormat.format(value),
                  'Available recorded cases',
                ]}
                labelFormatter={(year) => `Year ${year}`}
              />
              <Line
                type="monotone"
                dataKey="violations"
                name="Recorded cases"
                stroke="#35cbbf"
                strokeWidth={2.5}
                dot={{
                  r: 3,
                  fill: '#35cbbf',
                  stroke: '#10202c',
                  strokeWidth: 2,
                }}
                activeDot={{
                  r: 5,
                  fill: '#35cbbf',
                  stroke: '#10202c',
                  strokeWidth: 2,
                }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <ChartEmpty />
      )}

      <div className="violation-chart-footer">
        <span>2025 is incomplete; earlier years may also have missing categories</span>
        <span>HISTORICAL DATA</span>
      </div>
    </section>
  )
}

function AreaChartPanel({ data }) {
  return (
    <section className="panel violation-chart-card area-comparison-card">
      <ChartHeading
        eyebrow="AREA COMPARISON"
        title="Violations by area"
        subtitle="Illustrative sample counts across Bengaluru areas"
        demo
      />

      {data.length ? (
        <div className="violation-area-chart">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data}
              margin={{ top: 13, right: 8, left: -18, bottom: 0 }}
            >
              <CartesianGrid
                stroke="#1c2b3d"
                strokeDasharray="3 5"
                vertical={false}
              />
              <XAxis
                dataKey="name"
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#718398', fontSize: 8 }}
                interval={0}
                dy={8}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#718398', fontSize: 9 }}
              />
              <Tooltip
                contentStyle={tooltipStyle}
                formatter={(value) => [
                  numberFormat.format(value),
                  'Illustrative sample count',
                ]}
              />
              <Bar
                dataKey="violations"
                name="Violations"
                fill="#4e91f5"
                radius={[4, 4, 0, 0]}
                maxBarSize={34}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <ChartEmpty />
      )}

      <div className="violation-chart-footer">
        <span>Not connected to actual area-level records</span>
        <span>DEMO DATA</span>
      </div>
    </section>
  )
}

function ViolationTable({ rows, total, hasRecords }) {
  return (
    <section className="panel violation-table-card">
      <div className="panel-heading violation-table-heading">
        <div>
          <div className="eyebrow">
            DETAILED BREAKDOWN <HistoricalTag />
          </div>
          <h2>Top violation categories</h2>
          <p>Ranked offence counts and share within the displayed top 10</p>
        </div>
        <span className="table-result-count">{rows.length} categories</span>
      </div>

      <div className="violation-table-scroll">
        <table className="violation-table">
          <thead>
            <tr>
              <th>RANK</th>
              <th>VIOLATION CATEGORY</th>
              <th>NUMBER OF CASES</th>
              <th>PERCENTAGE SHARE</th>
            </tr>
          </thead>

          <tbody>
            {hasRecords ? (
              rows.map((row) => (
                <tr key={row.name}>
                  <td className="table-number">#{row.rank}</td>
                  <td>
                    <span
                      className="category-color"
                      style={{ background: row.color }}
                    />
                    <strong>{row.name}</strong>
                  </td>
                  <td className="table-number">
                    {numberFormat.format(row.count)}
                  </td>
                  <td>
                    <div className="share-cell">
                      <span>{row.share}%</span>
                      <i>
                        <b
                          style={{
                            width: `${row.share}%`,
                            background: row.color,
                          }}
                        />
                      </i>
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td className="violation-table-empty" colSpan="4">
                  <CircleAlert size={17} />
                  <strong>No matching records</strong>
                  <span>Try selecting another year or category.</span>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="violation-chart-footer">
        <span>These are recorded cases, not estimates of violation prevalence</span>
        <span>{numberFormat.format(total)} top 10 cases</span>
      </div>
    </section>
  )
}

export default function ViolationAnalytics() {
  const [year, setYear] = useState('2024')
  const [category, setCategory] = useState('All categories')

  const [yearlyData, setYearlyData] = useState([])
  const [top10Data, setTop10Data] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    async function loadViolationData() {
      try {
        setLoading(true)
        setError('')

        const [yearlyResponse, top10Response] = await Promise.all([
          getMotorVehicleYearly(),
          getMotorVehicleTop10(),
        ])

        if (!active) return

        setYearlyData(yearlyResponse.data || [])
        setTop10Data(top10Response.data || [])
      } catch (err) {
        if (active) {
          setError(
            err.response?.data?.detail ||
            err.message ||
            'Unable to load violation analytics.'
          )
        }
      } finally {
        if (active) setLoading(false)
      }
    }

    loadViolationData()

    return () => {
      active = false
    }
  }, [])

  const selectedYearData = useMemo(
    () => yearlyData.find((item) => String(item.year) === year),
    [yearlyData, year]
  )

  const selectedYearTop10 = useMemo(
    () =>
      top10Data
        .filter((item) => String(item.year) === year)
        .sort((a, b) => a.rank - b.rank),
    [top10Data, year]
  )

  const categoryOptions = useMemo(
    () => [
      { value: 'All categories', label: 'All categories' },
      ...selectedYearTop10.map((item) => ({
        value: item.offence_type,
        label: item.offence_type,
      })),
    ],
    [selectedYearTop10]
  )

  const categoryRows = useMemo(() => {
    const palette = violationCategories.map((item) => item.color)

    const rows = selectedYearTop10.map((item, index) => ({
      name: item.offence_type,
      count: Math.round(item.cases || 0),
      rank: item.rank,
      color: palette[index % palette.length],
    }))

    const filtered =
      category === 'All categories'
        ? rows
        : rows.filter((item) => item.name === category)

    const displayedTotal = filtered.reduce(
      (sum, item) => sum + item.count,
      0
    )

    return filtered.map((item) => ({
      ...item,
      share: displayedTotal
        ? Number(((item.count / displayedTotal) * 100).toFixed(1))
        : 0,
    }))
  }, [selectedYearTop10, category])

  const top10Total = useMemo(
    () => categoryRows.reduce((sum, item) => sum + item.count, 0),
    [categoryRows]
  )

  const kpis = useMemo(() => {
    const findCount = (offenceName) => {
      const record = selectedYearTop10.find(
        (item) => item.offence_type === offenceName
      )
      return record ? record.cases : null
    }

    return [
      {
        key: 'total',
        title: 'Total recorded cases',
        value: selectedYearData?.available_cases || 0,
        icon: ShieldAlert,
        tone: 'cyan',
      },
      {
        key: 'rider',
        title: 'Rider without helmet',
        value: findCount('Rider- without Helmet'),
        icon: HardHat,
        tone: 'blue',
      },
      {
        key: 'pillion',
        title: 'Pillion without helmet',
        value: findCount('Pillion Rider- without Helmet'),
        icon: HardHat,
        tone: 'violet',
      },
      {
        key: 'signal',
        title: 'Signal jumping',
        value: findCount('Jumping traffic signal'),
        icon: RadioTower,
        tone: 'amber',
      },
    ]
  }, [selectedYearData, selectedYearTop10])

  const trendData = useMemo(
    () =>
      [...yearlyData]
        .sort((a, b) => a.year - b.year)
        .map((item) => ({
          year: item.year,
          violations: Math.round(item.available_cases || 0),
        })),
    [yearlyData]
  )

  // This chart intentionally remains illustrative until a real
  // area-level violation endpoint is available.
  const areaData = useMemo(
    () =>
      violationAreas
        .map((item) => ({
          name: item.name,
          violations: demoViolationRecords
            .filter((record) => record.area === item.name)
            .reduce((sum, record) => sum + record.count, 0),
        }))
        .filter((item) => item.violations > 0),
    []
  )

  const isPartialYear =
    selectedYearData?.annual_total_status !== 'complete'

  if (loading) {
    return (
      <div className="page-content violation-page">
        <div className="violation-chart-empty">
          <strong>Loading violation analytics...</strong>
          <span>Fetching historical Bengaluru offence records.</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page-content violation-page">
        <div className="violation-chart-empty">
          <CircleAlert size={18} />
          <strong>Unable to load violation analytics</strong>
          <span>{error}</span>
        </div>
      </div>
    )
  }

  return (
    <div className="page-content violation-page">
      <div className="page-heading violation-page-heading">
        <div>
          <div className="eyebrow page-eyebrow">
            CITY INTELLIGENCE <span className="heading-separator">/</span>{' '}
            TRAFFIC ENFORCEMENT
          </div>
          <h1>Violation Analytics</h1>
          <p>
            Explore recorded traffic offences and enforcement trends across
            Bengaluru.
          </p>
        </div>
        <HistoricalTag />
      </div>

      <div className="violation-demo-notice">
        <CircleAlert size={15} />
        <span>
          <strong>DATA NOTE</strong> · Historical Motor Vehicle Act records
          are used for annual totals and offence rankings. Area comparisons
          remain illustrative sample data.
        </span>
      </div>

      <section className="violation-filters panel">
        <div className="violation-filter-title">
          <span>
            <BarChart3 size={15} />
          </span>
          <div>
            <strong>Filters</strong>
            <small>Update historical analytics</small>
          </div>
        </div>

        <FilterSelect
          label="Year"
          value={year}
          onChange={(value) => {
            setYear(value)
            setCategory('All categories')
          }}
          options={yearOptions.map((item) => ({
            value: String(item),
            label: item === 2025 ? '2025 (Partial)' : String(item),
          }))}
        />

        <FilterSelect
          label="Violation category"
          value={category}
          onChange={setCategory}
          options={categoryOptions}
        />

        <span className="violation-filter-demo">
          {isPartialYear
            ? 'Selected year has incomplete category coverage'
            : 'Selected year has complete category coverage'}
        </span>
      </section>

      {isPartialYear && (
        <div className="violation-demo-notice">
          <CircleAlert size={15} />
          <span>
            <strong>PARTIAL DATA</strong> · {year} has{' '}
            {selectedYearData?.reported_offence_categories ?? 0} of{' '}
            {selectedYearData?.total_expected_categories ?? 40} expected
            offence categories reported. Its available case count is not a
            complete annual total.
          </span>
        </div>
      )}

      <div className="kpi-grid violation-kpi-grid">
        {kpis.map((metric) => (
          <MetricCard
            key={metric.key}
            definition={metric}
            value={metric.value}
          />
        ))}
      </div>

      <div className="violation-charts-grid">
        <DistributionChart
          data={categoryRows}
          total={top10Total}
        />
        <TrendChart data={trendData} />
        <AreaChartPanel data={areaData} />
      </div>

      <ViolationTable
        rows={categoryRows}
        total={top10Total}
        hasRecords={categoryRows.length > 0}
      />

      <div className="violation-page-footer">
        <span>
          Annual totals and offence rankings reflect the selected year.
        </span>
        <span>AREA COMPARISON · DEMO DATA</span>
      </div>
    </div>
  )
}
