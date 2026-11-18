import { useEffect, useRef, useState } from 'react'
import type { ParkingSpace } from '../api/parking'
import type { ModelViewerElement } from '@google/model-viewer'

export function sameStay(first: ParkingSpace, other?: ParkingSpace) {
  return other?.status === 'occupied' && first.space_id === other.space_id &&
    first.vehicle_id === other.vehicle_id && first.last_updated === other.last_updated
}

function CarPreview() {
  const mount = useRef<HTMLDivElement>(null)
  const [state, setState] = useState<'loading' | 'ready' | 'failed'>('loading')
  useEffect(() => {
    let cancelled = false
    let viewer: ModelViewerElement | undefined
    const ready = () => setState('ready')
    const failed = () => setState('failed')
    import('@google/model-viewer').then(() => {
      if (cancelled || !mount.current) return
      viewer = document.createElement('model-viewer') as ModelViewerElement
      viewer.addEventListener('load', ready)
      viewer.addEventListener('error', failed)
      viewer.setAttribute('alt', 'Interactive BMW i8 vehicle preview')
      viewer.setAttribute('camera-controls', '')
      viewer.setAttribute('camera-orbit', '35deg 65deg auto')
      viewer.setAttribute('shadow-intensity', '0.7')
      viewer.src = import.meta.env.BASE_URL + 'models/bmw_i8.glb'
      mount.current.appendChild(viewer)
    }).catch(() => { if (!cancelled) failed() })
    return () => {
      cancelled = true
      viewer?.removeEventListener('load', ready)
      viewer?.removeEventListener('error', failed)
      viewer?.remove()
    }
  }, [])
  return <figure>
    <div className={`vehicle-stage preview-${state}`}>
      <div ref={mount} className="viewer-mount" />
      {state !== 'ready' && <span role="status">{state === 'failed' ? '3D preview unavailable' : 'Loading vehicle preview…'}</span>}
    </div>
    <figcaption>BMW i8 preview · <a href="https://sketchfab.com/3d-models/bmw-i8-4b143b95aec045bf8912d99662f8d580">iSteven</a> · <a href="https://creativecommons.org/licenses/by-nc/4.0/">CC BY-NC 4.0</a></figcaption>
  </figure>
}

function ParkedTime({ arrival }: { arrival: string }) {
  const [now, setNow] = useState(Date.now)
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(timer)
  }, [])
  const seconds = Math.max(0, Math.floor((now - Date.parse(arrival)) / 1000))
  const hours = Math.floor(seconds / 3600)
  return <>{hours > 0 && `${hours}h `}{Math.floor(seconds / 60) % 60}m {seconds % 60}s</>
}

export function VehicleInspector({ stay, current, stale, close }: {
  stay: ParkingSpace; current?: ParkingSpace; stale: boolean; close: () => void
}) {
  const dialog = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const element = dialog.current!
    element.showModal()
    return () => element.close()
  }, [])
  const active = sameStay(stay, current)
  return <dialog className="vehicle-sheet" ref={dialog} aria-labelledby="vehicle-title"
    onCancel={event => { event.preventDefault(); close() }}
    onClick={event => { if (event.target === dialog.current) close() }}>
    <article>
      <header><div><p>Vehicle details</p><h2 id="vehicle-title">{stay.vehicle_id}</h2></div>
        <button className="button secondary" type="button" autoFocus onClick={close}>Close</button></header>
      <CarPreview />
      <dl><div><dt>Parking bay</dt><dd>{stay.space_id}</dd></div>
        <div><dt>Status</dt><dd role="status">{active ? stale ? 'Last seen occupied' : 'Occupied' : 'Stay ended'}</dd></div>
        <div><dt>Arrival</dt><dd><time dateTime={stay.last_updated}>{new Date(stay.last_updated).toLocaleString()}</time></dd></div>
        {active && !stale && <div><dt>Time parked</dt><dd><ParkedTime arrival={stay.last_updated} /></dd></div>}
      </dl>
    </article>
  </dialog>
}
