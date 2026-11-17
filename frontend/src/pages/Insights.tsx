import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart,
  Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { getAnalytics, getFacilities, getForecast } from '../api/parking'
import type { Analytics, Forecast } from '../api/parking'
import { Icon } from '../components/Icon'
import { ForecastProcess } from '../components/ForecastProcess'

const chartColors = {
  recorded: 'var(--color-accent)',
  recordedFill: 'var(--color-accent-soft)',
  secondary: 'var(--color-chart-secondary)',
  forecast: 'var(--color-forecast-ink)',
  grid: 'var(--color-rule)',
  text: 'var(--color-muted)',
}
const tooltipStyle = {
  color: 'var(--color-ink)',
  borderRadius: 12,
  border: '1px solid var(--color-rule)',
  background: 'var(--color-surface)',
}
const replayTime = new Intl.DateTimeFormat('en-GB', {
  timeZone: 'Europe/London',
  month: 'short',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  timeZoneName: 'short',
})

function formatClock(timestamp: string) {
  return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function AnalyticsCharts({ analytics }: { analytics: Analytics }) {
  const hourly = analytics.hourly.map(item => ({ ...item, total: item.arrivals + item.departures }))
  const peakCount = Math.max(0, ...hourly.map(item => item.total))
  const peak = hourly.filter(item => item.total === peakCount && peakCount > 0)
  const busiest = analytics.spaces.filter(space => space.arrivals > 0)
    .sort((a, b) => b.arrivals - a.arrivals || a.space_id.localeCompare(b.space_id)).slice(0, 5)
  const usage = [
    { name: 'No arrivals', value: analytics.spaces.filter(space => space.arrivals === 0).length, color: 'var(--color-rule)' },
    { name: '1–4 arrivals', value: analytics.spaces.filter(space => space.arrivals >= 1 && space.arrivals < 5).length, color: chartColors.secondary },
    { name: '5+ arrivals', value: analytics.spaces.filter(space => space.arrivals >= 5).length, color: chartColors.recorded },
  ]

  return <div className="insights-grid">
    <section className="card chart-card chart-wide" aria-label="Recorded occupancy">
      <div className="card-header">
        <div><h3>Recorded occupancy</h3><p>Up to the last 240 accepted events</p></div>
        <span className="category-tag">Simulated data</span>
      </div>
      <div className="chart-shell" role="img" aria-label="Occupied bays over time">
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={analytics.points} margin={{ top: 12, right: 20, left: -20, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 5" stroke={chartColors.grid} vertical={false} />
            <XAxis dataKey="timestamp" tick={{ fill: chartColors.text, fontSize: 11 }}
              axisLine={false} tickLine={false} tickFormatter={formatClock} minTickGap={26} />
            <YAxis domain={[0, analytics.capacity]} allowDecimals={false}
              tick={{ fill: chartColors.text, fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip labelFormatter={value => new Date(String(value)).toLocaleString()} contentStyle={tooltipStyle} />
            <Area type="stepAfter" dataKey="occupied" name="Occupied bays" stroke={chartColors.recorded}
              fill={chartColors.recordedFill} strokeWidth={2.5} isAnimationActive={false}
              dot={analytics.points.length === 1 ? { r: 4 } : false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
    <section className="card chart-card" aria-label="Most-used bays">
      <div className="card-header"><div><h3>Most-used bays</h3><p>Ranked by recorded arrivals</p></div></div>
      {busiest.length ? <ol className="busiest-list">
        {busiest.map(space => <li key={space.space_id}>
          <span>{space.space_id}</span>
          <progress value={space.arrivals} max={busiest[0].arrivals} aria-label={`${space.space_id} arrivals`} />
          <strong>{space.arrivals}</strong>
        </li>)}
      </ol> : <p className="quiet-state">No arrivals recorded.</p>}
    </section>

    <section className="card chart-card chart-wide" aria-label="Arrivals and departures by hour">
      <div className="card-header">
        <div><h3>Arrivals and departures</h3>
          <p>{analytics.total_arrivals} arrivals and {analytics.total_departures} departures, grouped by UTC hour</p></div>
      </div>
      <div className="chart-shell" role="img" aria-label="Hourly arrivals and departures in UTC">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={hourly} margin={{ top: 8, right: 16, left: -20, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 5" stroke={chartColors.grid} vertical={false} />
            <XAxis dataKey="hour" tick={{ fill: chartColors.text, fontSize: 11 }} axisLine={false} tickLine={false} minTickGap={18} />
            <YAxis allowDecimals={false} tick={{ fill: chartColors.text, fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={tooltipStyle} />
            <Legend iconType="circle" />
            <Bar dataKey="arrivals" name="Arrivals" fill={chartColors.recorded} radius={[3, 3, 0, 0]} isAnimationActive={false} />
            <Bar dataKey="departures" name="Departures" fill={chartColors.secondary} radius={[3, 3, 0, 0]} isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      {!!peak.length && <p className="chart-note">
        Peak {peak.length > 1 ? 'periods' : 'period'} {peak.map(item => item.hour).join(', ')} UTC
        <span className="category-tag">{peakCount} events per hour</span>
      </p>}
    </section>
    <section className="card chart-card" aria-label="Bay usage distribution">
      <div className="card-header"><div><h3>Bay usage</h3><p>Grouped by total arrivals per bay</p></div></div>
      <div className="chart-shell" role="img" aria-label="Distribution of bays across arrival count groups">
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie data={usage} dataKey="value" nameKey="name" innerRadius={50} outerRadius={73}
              paddingAngle={3} stroke="none" isAnimationActive={false}>
              {usage.map(group => <Cell key={group.name} fill={group.color} />)}
            </Pie>
            <Tooltip contentStyle={tooltipStyle} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <ul className="chart-key">
        {usage.map(group => <li key={group.name}><i style={{ background: group.color }} />{group.name}<strong>{group.value}</strong></li>)}
      </ul>
    </section>
  </div>
}

function ForecastChart({ forecast }: { forecast: Forecast }) {
  const series = [
    ...forecast.history.filter(entry => Date.parse(entry.timestamp) < Date.parse(forecast.reference_at))
      .map(entry => ({ timestamp: entry.timestamp, Recorded: entry.occupancy })),
    {
      timestamp: forecast.reference_at,
      Recorded: forecast.current_occupancy,
      Forecast: forecast.current_occupancy,
    },
    {
      timestamp: forecast.target_at,
      Forecast: forecast.predicted_occupancy,
      Actual: forecast.actual_occupancy ?? undefined,
    },
  ]
  return <div className="chart-shell" role="img" aria-label="Recorded Birmingham occupancy and dashed 30-minute forecast">
    <ResponsiveContainer width="100%" height={265}>
      <LineChart data={series} margin={{ top: 12, right: 20, left: -15, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 5" stroke={chartColors.grid} vertical={false} />
        <XAxis dataKey="timestamp" tick={{ fill: chartColors.text, fontSize: 11 }} axisLine={false}
          tickLine={false} minTickGap={22}
          tickFormatter={value => new Date(value).toLocaleTimeString('en-GB', {
            timeZone: 'Europe/London', hour: '2-digit', minute: '2-digit',
          })} />
        <YAxis domain={[0, forecast.capacity]} allowDecimals={false} axisLine={false} tickLine={false}
          tick={{ fill: chartColors.text, fontSize: 11 }} />
        <Tooltip labelFormatter={value => replayTime.format(new Date(String(value)))} contentStyle={tooltipStyle} />
        <Legend iconType="plainline" />
        <Line dataKey="Recorded" stroke={chartColors.secondary} strokeWidth={2.4} dot={false} isAnimationActive={false} />
        <Line dataKey="Forecast" stroke={chartColors.forecast} strokeDasharray="7 5" strokeWidth={2.6}
          dot={{ r: 4, fill: chartColors.forecast }} isAnimationActive={false} />
        {forecast.actual_occupancy !== null && <Line dataKey="Actual" stroke={chartColors.recorded}
          dot={{ r: 5, fill: chartColors.recorded }} isAnimationActive={false} />}
      </LineChart>
    </ResponsiveContainer>
  </div>
}

function ForecastReplay() {
  const facilities = useQuery({ queryKey: ['facilities'], queryFn: ({ signal }) => getFacilities(signal) })
  const [facilityId, setFacilityId] = useState('')
  const [reference, setReference] = useState('')
  const [comparison, setComparison] = useState<string>()
  const facility = facilities.data?.facilities.find(item => item.facility_id === facilityId) ?? facilities.data?.facilities[0]
  const referenceTime = reference || facility?.last_reference_at
  const forecast = useQuery({
    queryKey: ['forecast', facility?.facility_id, referenceTime, comparison],
    enabled: !!facility,
    queryFn: ({ signal }) => getForecast({
      facility_id: facility!.facility_id,
      reference_at: referenceTime,
      as_of: comparison,
    }, signal),
  })
  const result = forecast.data
  const error = facilities.error ?? forecast.error

  return <section className="card forecast-card" aria-label="Birmingham occupancy forecast replay">
    <div className="card-header">
      <div><h3>Birmingham forecast replay</h3><p>Historical observations from UCI Parking Birmingham</p></div>
      <span className="category-tag forecast-tag">Forecast, not live</span>
    </div>
    {error ? <div className="empty-state forecast-empty">
      <span className="empty-icon"><Icon name="alert" /></span><strong>Forecast unavailable</strong>
      <span>{error.message}</span>
      <button className="button secondary" type="button" onClick={() => {
        if (facilities.error) void facilities.refetch()
        else void forecast.refetch()
      }}>Retry forecast</button>
    </div>
      : facilities.isPending ? <p className="quiet-state" role="status">Loading replay facilities…</p>
      : !facility ? <p className="quiet-state">No Birmingham facilities are available for replay.</p>
      : <>
        <div className="forecast-controls">
          <label htmlFor="replay-facility">Birmingham facility
            <select id="replay-facility" value={facility.facility_id} onChange={event => {
              setFacilityId(event.currentTarget.value)
              setReference('')
              setComparison(undefined)
            }}>
              {facilities.data?.facilities.map(item => <option key={item.facility_id}>{item.facility_id}</option>)}
            </select>
          </label>
          <label htmlFor="replay-reference">Historical reference time
            <select id="replay-reference" value={referenceTime} onChange={event => {
              setReference(event.currentTarget.value)
              setComparison(undefined)
            }}>
              {(facility.reference_times ?? [facility.last_reference_at]).slice().reverse().map(timestamp =>
                <option value={timestamp} key={timestamp}>{replayTime.format(new Date(timestamp))}</option>)}
            </select>
          </label>
          <button className="button secondary compare-button" type="button"
            disabled={!result || result.actual_occupancy !== null}
            onClick={() => { if (result) setComparison(result.target_at) }}>
            {result?.actual_occupancy != null ? 'Actual shown' : 'Reveal actual at target time'}
          </button>
        </div>
        {result ? <div className="forecast-result">
          <ForecastChart forecast={result} />
          <div className="forecast-detail">
            <span className="stat-label">{result.horizon_minutes}-minute forecast</span>
            <strong>{Math.round(result.predicted_occupancy)} <small>of {result.capacity} occupied</small></strong>
            <span>About {Math.round(result.predicted_free_spaces)} free at {replayTime.format(new Date(result.target_at))}</span>
            <span>Model <b>{result.model_name}</b></span>
            {result.actual_occupancy !== null && <span className="actual-value">
              Actual at target time <b>{result.actual_occupancy} occupied</b>
              {result.actual_free_spaces !== null && <>, {result.actual_free_spaces} free</>}
            </span>}
            <dl className="model-metrics" aria-label="Historical holdout metrics">
              <div><dt>MAE</dt><dd>{result.metrics.mae.toFixed(2)} spaces</dd></div>
              <div><dt>RMSE</dt><dd>{result.metrics.rmse.toFixed(2)} spaces</dd></div>
              <div><dt>R²</dt><dd>{result.metrics.r2?.toFixed(3) ?? '—'}</dd></div>
            </dl>
            <span>Measured on Birmingham’s historical holdout data.</span>
          </div>
        </div> : <p className="quiet-state" role="status">Loading the historical forecast…</p>}
        {result?.explanation && <ForecastProcess explanation={result.explanation} model={result.model_name}
          occupied={result.predicted_occupancy} capacity={result.capacity} />}
      </>}
  </section>
}

export function Insights() {
  const analytics = useQuery({
    queryKey: ['analytics'],
    queryFn: ({ signal }) => getAnalytics(signal),
    refetchInterval: 5000,
  })
  return <div className="insights-page">
    <div className="section-heading">
      <h2>Simulated lot activity</h2>
      <a className="text-button" href="#events">View events <Icon name="arrowRight" size={17} /></a>
    </div>
    {analytics.error ? <div className="card empty-state" role="status">
      <strong>Analytics unavailable</strong><span>{analytics.error.message}</span>
      <button className="button secondary" type="button" onClick={() => { void analytics.refetch() }}>Retry analytics</button>
    </div> : analytics.isPending ? <div className="card empty-state" role="status">Loading recorded activity…</div>
      : analytics.data.points.length === 0 ? <div className="card empty-state">
        <span className="empty-icon"><Icon name="insights" /></span><strong>No recorded activity yet</strong>
        <span>Send a parking event to fill the analytics charts.</span>
        <a className="button secondary" href="#simulate">Open simulation</a>
      </div> : <AnalyticsCharts analytics={analytics.data} />}
    <div className="section-heading forecast-heading"><h2>Historical occupancy forecast</h2></div>
    <ForecastReplay />
  </div>
}
