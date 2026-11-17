import { useState } from 'react'
import type { ParkingEvent, ParkingSpace } from '../api/parking'
import { EventList } from '../components/Events'
import { Icon } from '../components/Icon'
import { Lot } from '../components/Lot'
import { ArrivalForecast } from '../components/ArrivalForecast'

function OccupancyRing({ percent }: { percent?: number }) {
  return <svg className="occupancy-ring" viewBox="0 0 52 52" aria-hidden="true">
    <circle className="ring-track" cx="26" cy="26" r="21" />
    {percent !== undefined && percent > 0 && <circle className="ring-value" cx="26" cy="26" r="21"
      pathLength="100" strokeDasharray={`${percent} 100`} transform="rotate(-90 26 26)" />}
  </svg>
}

function occupancyTrend(events: ParkingEvent[], spaces: ParkingSpace[], current: number) {
  const lastChange = spaces.reduce((latest, space) => Math.max(latest, Date.parse(space.last_updated)), 0)
  const points = []
  let occupied = current
  for (const event of events.filter(event => Date.parse(event.timestamp) <= lastChange).slice(0, 18)) {
    points.unshift(occupied)
    occupied += event.event_type === 'SPACE_OCCUPIED' ? -1 : 1
  }
  return points
}

function TrendSparkline({ activity, capacity }: { activity: number[]; capacity: number }) {
  const points = activity.map((value, index) => [
    2 + index * (96 / (activity.length - 1)),
    38 - value * (36 / capacity),
  ])
  const steps = points.flatMap(([x, y], index) =>
    index ? [`${x},${points[index - 1][1]}`, `${x},${y}`] : [`${x},${y}`]).join(' ')
  return <svg className="trend-sparkline" viewBox="0 0 100 40" preserveAspectRatio="none" aria-hidden="true">
    <polygon points={`2,40 ${steps} 98,40`} />
    <polyline points={steps} vectorEffect="non-scaling-stroke" />
  </svg>
}

export function LiveLot({ inspect, spaces, events }: { inspect: (space: ParkingSpace) => void; spaces?: ParkingSpace[]; events?: ParkingEvent[] }) {
  const [selected, setSelected] = useState<'available' | 'occupied'>('available')
  const capacity = spaces?.length
  const available = spaces?.filter(space => space.status === 'available').length
  const occupied = spaces?.filter(space => space.status === 'occupied').length
  const percent = capacity && occupied !== undefined ? Math.round(occupied / capacity * 100) : undefined
  const activity = events && spaces && occupied !== undefined ? occupancyTrend(events, spaces, occupied) : []
  const matching = spaces?.filter(space => space.status === selected)

  return (
    <div className="live-grid">
      <section className="card lot-card" aria-label="Live parking layout">
        <div className="card-header">
          <div><h2>Lot overview</h2><p>Simulated facility</p></div>
          <span className="location-pill"><Icon name="lot" size={17} /> {capacity ?? '—'} bays</span>
        </div>
        <Lot inspect={inspect} spaces={spaces} />
        <div className="lot-summary">
          <div className="occupancy-stat">
            <OccupancyRing percent={percent} />
            <div>
              <span className="stat-label">Lot occupancy</span>
              <strong>{percent !== undefined ? `${percent}%` : '—'}</strong>
              <span>{occupied ?? '—'} of {capacity ?? '—'} bays occupied</span>
            </div>
          </div>
          <div className="trend-stat" role="img" aria-label="Recent simulated occupancy trend">
            <div><span className="stat-label">Usage trend</span><span>Recent accepted events</span></div>
            {capacity && activity.length > 1
              ? <TrendSparkline activity={activity} capacity={capacity} />
              : <span className="trend-empty">More activity needed</span>}
          </div>
        </div>
      </section>

      <ArrivalForecast />

      <div className="live-side">
        <section className="card side-card spaces-card">
          <div className="card-header"><div><h2>Parking spaces</h2><p>Current availability</p></div></div>
          <div className="filters" aria-label="Show parking bays by status">
            <button className="filter-button" aria-pressed={selected === 'available'} type="button"
              onClick={() => setSelected('available')}>Available <strong>{available ?? '—'}</strong></button>
            <button className="filter-button" aria-pressed={selected === 'occupied'} type="button"
              onClick={() => setSelected('occupied')}>Occupied <strong>{occupied ?? '—'}</strong></button>
          </div>
          <div className="space-chips" aria-label={`${selected} bays`}>
            {matching ? matching.length
              ? matching.map(space => space.status === 'occupied'
                ? <button type="button" className="space-chip occupied" key={space.space_id}
                    aria-label={`Inspect ${space.vehicle_id} in ${space.space_id}`} onClick={() => inspect(space)}>{space.space_id}</button>
                : <span className="space-chip available" key={space.space_id}>{space.space_id}</span>)
              : <span className="quiet-state">No {selected} bays.</span>
              : <span className="quiet-state">Waiting for parking spaces…</span>}
          </div>
        </section>
        <section className="card side-card activity-card">
          <div className="card-header">
            <div><h2>Recent activity</h2><p>Latest accepted events</p></div>
            <a className="icon-link" href="#events" aria-label="View all recent events"><Icon name="arrowRight" size={19} /></a>
          </div>
          <EventList events={events} count={5} />
        </section>
      </div>
    </div>
  )
}
