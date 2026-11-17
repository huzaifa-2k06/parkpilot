import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { getLiveFacilities, getLiveForecast } from '../api/parking'
import { ForecastCapacityMap } from './ForecastCapacityMap'
import { ForecastProcess } from './ForecastProcess'

function toLocalFields(date: Date) {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000).toISOString()
  return { day: local.slice(0, 10), time: local.slice(11, 16) }
}

const formatArrival = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' })
const formatObservation = new Intl.DateTimeFormat(undefined, { timeStyle: 'medium' })

export function ArrivalForecast() {
  const [facilityId, setFacilityId] = useState('')
  const [fields, setFields] = useState(() => toLocalFields(new Date(Date.now() + 15 * 60_000)))
  const [selection, setSelection] = useState<{ facility: string; arrival: string }>()
  const [inputError, setInputError] = useState('')
  const facilities = useQuery({
    queryKey: ['live-facilities'],
    queryFn: ({ signal }) => getLiveFacilities(signal),
    refetchInterval: 30_000,
  })
  const facility = facilities.data?.find(item => item.id === facilityId) ?? facilities.data?.[0]
  const forecast = useQuery({
    queryKey: ['live-forecast', selection?.facility, selection?.arrival],
    enabled: !!selection,
    queryFn: ({ signal }) => getLiveForecast(selection!.facility, selection!.arrival, signal),
    refetchInterval: () => selection && Date.parse(selection.arrival) > Date.now() ? 5_000 : false,
  })
  const latest = facility ? toLocalFields(new Date(Date.now() + facility.max_horizon_minutes * 60_000)) : undefined
  const expired = selection && Date.parse(selection.arrival) <= Date.now()
  const result = !expired && !forecast.isError ? forecast.data : undefined
  const windowLabel = facility && (facility.max_horizon_minutes > 1440
    ? '7 days' : facility.max_horizon_minutes > 30 ? '24 hours' : '30 minutes')

  function resetForecast() {
    setSelection(undefined)
    setInputError('')
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!facility) return
    const arrival = new Date(`${fields.day}T${fields.time}`)
    if (Number.isNaN(arrival.getTime()) || toLocalFields(arrival).time !== fields.time) {
      setInputError('Choose a valid local date and time.')
      return
    }
    if (arrival.getTime() <= Date.now() ||
        arrival.getTime() > Date.now() + facility.max_horizon_minutes * 60_000) {
      setInputError(`Choose an arrival within the next ${windowLabel}.`)
      return
    }
    setInputError('')
    setSelection({ facility: facility.id, arrival: arrival.toISOString() })
  }

  return <section className="card arrival-card" aria-label="Arrival forecast">
    <div className="card-header">
      <div><h2>Plan your arrival</h2>
        <p>{windowLabel ? `Next ${windowLabel}. Times use your device’s timezone.` : 'Simulated facility forecast'}</p>
      </div>
      <span className="category-tag forecast-tag">Forecast</span>
    </div>
    <form className="forecast-controls" onSubmit={submit}>
      <label>Facility
        <select value={facility?.id ?? ''} disabled={!facility} onChange={event => {
          resetForecast()
          setFacilityId(event.currentTarget.value)
        }}>
          {facility ? facilities.data?.map(item => <option key={item.id} value={item.id}>{item.name}</option>)
            : <option value="">Facility unavailable</option>}
        </select>
      </label>
      <label>Day
        <input type="date" required value={fields.day} min={toLocalFields(new Date()).day} max={latest?.day}
          onChange={event => { resetForecast(); setFields({ ...fields, day: event.currentTarget.value }) }} />
      </label>
      <label>Arrival time
        <input type="time" required value={fields.time}
          onChange={event => { resetForecast(); setFields({ ...fields, time: event.currentTarget.value }) }} />
      </label>
      <button className="button primary" type="submit" disabled={!facility || (!!selection && forecast.isPending)}>
        Estimate availability
      </button>
    </form>
    {(inputError || facilities.error || (!expired && forecast.error)) && <p className="form-error" role="alert">
      {inputError || facilities.error?.message || forecast.error?.message}
    </p>}
    {expired && <p className="quiet-state" role="status">This arrival time has passed. Choose a new time.</p>}
    {selection && !expired && forecast.isPending && <p className="quiet-state" role="status">Estimating availability…</p>}
    {result && <>
    <div className="forecast-detail arrival-result">
      <span className="stat-label">Estimated at arrival · {formatArrival.format(new Date(result.arrival_at))}</span>
      <strong role="status">{result.estimated_free} <small>of {result.capacity} spaces free</small></strong>
      <span>{result.estimated_occupied} estimated occupied · {Math.ceil(result.horizon_minutes)} min ahead</span>
      <span>{result.model} · {result.source === 'simulated_calendar'
        ? 'Simulated weekday and time pattern'
        : `Simulated occupancy read at ${formatObservation.format(new Date(result.observed_at))}`}</span>
    </div>
    <ForecastCapacityMap capacity={result.capacity} occupied={result.estimated_occupied} />
    {result.explanation && <ForecastProcess explanation={result.explanation} model={result.model}
      capacity={result.capacity} occupied={result.estimated_occupied} />}
    </>}
  </section>
}
