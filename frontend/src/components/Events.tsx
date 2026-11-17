import { useState } from 'react'
import type { ParkingEvent } from '../api/parking'
import { Icon } from './Icon'

type Filter = 'all' | 'arrivals' | 'departures'
const filters: { value: Filter; title: string }[] = [
  { value: 'all', title: 'All activity' },
  { value: 'arrivals', title: 'Arrivals' },
  { value: 'departures', title: 'Departures' },
]

export function EventList({ events, count, filterable = false, accepted = false }: {
  events: ParkingEvent[] | undefined
  count?: number
  filterable?: boolean
  accepted?: boolean
}) {
  const [filter, setFilter] = useState<Filter>('all')
  const visible = events?.filter(event => filter === 'all' ||
    (filter === 'arrivals') === (event.event_type === 'SPACE_OCCUPIED')).slice(0, count)

  return (
    <>
      {filterable && <div className="filters" aria-label="Filter activity">
        {filters.map(({ value, title }) =>
          <button key={value} type="button" aria-pressed={filter === value}
            className="filter-button" onClick={() => setFilter(value)}>{title}</button>)}
      </div>}
      {events === undefined ? <p className="quiet-state">Waiting for event history…</p>
        : visible?.length === 0 ? <div className="empty-state">
          <span className="empty-icon"><Icon name="events" /></span>
          <strong>{filter === 'all' ? 'No activity yet' : `No ${filter} recorded`}</strong>
          <span>{filter === 'all' ? 'Accepted parking events will appear here.' : 'Try another activity filter.'}</span>
        </div>
        : <ul className="event-list">
          {visible?.map(event => {
            const arrival = event.event_type === 'SPACE_OCCUPIED'
            return <li className="event-row" key={event.event_id}>
              <span className={`event-icon ${arrival ? 'arrival' : 'departure'}`}>
                <Icon name={arrival ? 'arrowIn' : 'arrowOut'} size={17} />
              </span>
              <div className="event-copy"><strong>{event.space_id}</strong><span>{event.vehicle_id}</span></div>
              <span className={`event-tag ${arrival ? 'arrival' : 'departure'}`}>{arrival ? 'Arrived' : 'Left'}</span>
              {accepted && <span className="event-tag arrival">Accepted</span>}
              <time dateTime={event.timestamp} title={new Date(event.timestamp).toLocaleString()}>
                {new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </time>
            </li>
          })}
        </ul>}
    </>
  )
}
