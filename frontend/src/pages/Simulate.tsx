import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { ApiError, getSpeed, sendEvent, setRunning, setSpeed } from '../api/parking'
import type { ParkingEvent, ParkingSpace } from '../api/parking'
import { EventList } from '../components/Events'
import { Icon } from '../components/Icon'
import { Lot } from '../components/Lot'

export function Simulate({ spaces, events, running }: {
  spaces?: ParkingSpace[]
  events?: ParkingEvent[]
  running?: boolean
}) {
  const client = useQueryClient()
  const [draftSpeed, setDraftSpeed] = useState<number>()
  const speed = useQuery({ queryKey: ['speed'], queryFn: ({ signal }) => getSpeed(signal) })
  const controls = useMutation({
    mutationFn: setRunning,
    onSuccess(result) {
      client.setQueryData(['simulation'], result)
    },
  })
  const manual = useMutation({
    mutationFn: sendEvent,
    onSuccess() {
      void client.invalidateQueries({ queryKey: ['spaces'] })
      void client.invalidateQueries({ queryKey: ['events'] })
      void client.invalidateQueries({ queryKey: ['analytics'] })
    },
  })
  const speedControl = useMutation({
    mutationFn: setSpeed,
    onSuccess(result) {
      client.setQueryData(['speed'], result)
      setDraftSpeed(undefined)
    },
  })
  const shownSpeed = draftSpeed ?? speed.data?.speed ?? 1
  const manualError = manual.error

  return <div className="simulation-grid">
    <section className="card lot-card" aria-label="Simulation map and controls">
      <div className="card-header">
        <div><h2>Vehicle movement</h2><p>Accepted events appear on the lot</p></div>
        <span className="location-pill"><Icon name="simulate" size={17} /> Simulated lot</span>
      </div>
      <Lot spaces={spaces} mode="simulate" />
      <div className="control-dock">
        <h3>Automatic simulation</h3>
        <div className="control-buttons">
          <button className="button primary" type="button" disabled={running === undefined || controls.isPending}
            onClick={() => controls.mutate(!running)}>
            <Icon name={running ? 'pause' : 'play'} size={18} />
            {controls.isPending ? 'Updating…' : running ? 'Stop simulation' : 'Start simulation'}
          </button>

        </div>
        <div className="speed-control">
          <label htmlFor="simulation-speed">Auto speed <strong>{shownSpeed}×</strong></label>
          <input id="simulation-speed" type="range" value={shownSpeed} min="0.5" max="2" step="0.25"
            disabled={!speed.data || speedControl.isPending} onChange={event => setDraftSpeed(event.currentTarget.valueAsNumber)} />
          <button className="button secondary" type="button"
            disabled={!speed.data || shownSpeed === speed.data.speed || speedControl.isPending}
            onClick={() => speedControl.mutate(shownSpeed)}>Apply</button>
        </div>
        {(controls.error || speed.error || speedControl.error) &&
          <p className="form-error" role="alert">{(controls.error ?? speed.error ?? speedControl.error)?.message}</p>}
      </div>
    </section>
    <aside className="simulation-side" aria-label="Simulator results">
      <section className="card side-card">
        <div className="card-header"><div><h2>Manual events</h2></div></div>
        <div className="control-buttons manual-actions">
          <button className="button secondary" type="button" disabled={manual.isPending}
            onClick={() => manual.mutate('arrival')}><Icon name="arrowIn" size={18} /> Send arrival</button>
          <button className="button secondary" type="button" disabled={manual.isPending}
            onClick={() => manual.mutate('departure')}><Icon name="arrowOut" size={18} /> Send departure</button>
        </div>
        <div className="webhook-panel" role="status">
          {manual.isPending ? <p>Sending event…</p> : manual.data ? <>
            <span className="response-status response-success">HTTP 201 Accepted</span>
            <pre>{JSON.stringify(manual.data, null, 2)}</pre>
          </> : manualError ? <>
            <span className="response-status response-error">
              {manualError instanceof ApiError && manualError.status ? `HTTP ${manualError.status} Rejected` : 'Request failed'}
            </span>
            <pre>{JSON.stringify({ detail: manualError.message }, null, 2)}</pre>
          </> : <p>Send an arrival or departure to view the response.</p>}
        </div>
      </section>
      <section className="card side-card">
        <div className="card-header">
          <div><h2>Event history</h2><p>Accepted events</p></div>
          <a className="icon-link" href="#events" aria-label="View event history"><Icon name="arrowRight" size={19} /></a>
        </div>
        <EventList events={events} count={6} />
      </section>
    </aside>
  </div>
}
