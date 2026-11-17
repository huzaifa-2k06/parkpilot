import { motion, useReducedMotion } from 'framer-motion'
import { useEffect, useId, useRef, useState } from 'react'
import type { ParkingSpace } from '../api/parking'

type Trip = {
  id: number
  next: ParkingSpace
  vehicle: string
  arrival: boolean
  duration: number
}

type LotMotion = {
  spaces: ParkingSpace[]
  queue: Trip[]
  trip: Trip | null
  notice: Trip | null
}

const emptyMotion: LotMotion = { spaces: [], queue: [], trip: null, notice: null }
const lane = 222
const bayIds = Array.from({ length: 20 }, (_, i) => `P${String(i + 1).padStart(2, '0')}`)

function bayOf(spaceId: string) {
  const index = bayIds.indexOf(spaceId)
  const top = index < 10
  return {
    top,
    x: 198 + (index % 10) * 72,
    y: top ? 149 : 298,
    rotation: top ? -90 : 90,
  }
}

function advance(previous: LotMotion, queue: Trip[]): LotMotion {
  const [next, ...waiting] = queue
  if (!next) return { ...previous, queue: [], trip: null }
  return {
    ...previous,
    queue: waiting,
    trip: { ...next, duration: 3.3 / Math.min(2, 1 + waiting.length * 0.25) },
  }
}

function useLotMotion(spaces: ParkingSpace[] | undefined) {
  const [state, setState] = useState<LotMotion>(emptyMotion)
  const latest = useRef<ParkingSpace[] | undefined>(undefined)
  const nextTripId = useRef(0)

  useEffect(() => {
    if (!spaces) return
    const prior = latest.current
    latest.current = spaces
    if (!prior || document.hidden) {
      setState({ ...emptyMotion, spaces })
      return
    }
    const previous = new Map(prior.map(space => [space.space_id, space]))
    const changes: Trip[] = []
    for (const space of spaces) {
      const old = previous.get(space.space_id)
      if (!old || old.status === space.status) continue
      const arrival = space.status === 'occupied'
      const vehicle = arrival ? space.vehicle_id : old.vehicle_id
      if (vehicle && (arrival || space.status === 'available')) {
        changes.push({ id: nextTripId.current++, next: space, arrival, vehicle, duration: 0 })
      }
    }
    changes.sort((first, second) =>
      Date.parse(first.next.last_updated) - Date.parse(second.next.last_updated),
    )
    if (!changes.length) {
      setState(current => current.trip ? current : { ...current, spaces })
      return
    }
    setState(current => {
      const queue = [...current.queue, ...changes]
      if (queue.length > 8) return { ...emptyMotion, spaces }
      return current.trip ? { ...current, queue } : advance(current, queue)
    })
  }, [spaces])

  useEffect(() => {
    const sync = () => {
      if (latest.current) setState({ ...emptyMotion, spaces: latest.current })
    }
    document.addEventListener('visibilitychange', sync)
    return () => document.removeEventListener('visibilitychange', sync)
  }, [])

  useEffect(() => {
    if (!state.notice) return
    const id = window.setTimeout(() => setState(current => ({ ...current, notice: null })), 3200)
    return () => window.clearTimeout(id)
  }, [state.notice])

  const finishTrip = (id: number) => {
    setState(current => {
      if (current.trip?.id !== id) return current
      const completed = current.trip
      return advance({
        ...current,
        spaces: current.queue.length
          ? current.spaces.map(space => space.space_id === completed.next.space_id ? completed.next : space)
          : latest.current ?? current.spaces,
        notice: completed,
      }, current.queue)
    })
  }

  return { ...state, finishTrip }
}

function Car({ vehicle, brakes = false }: { vehicle: string; brakes?: boolean }) {
  const hash = Array.from(vehicle).reduce((acc, letter) => (Math.imul(acc, 31) + letter.charCodeAt(0)) >>> 0, 0)
  const width = [40, 45, 35][hash % 3]
  const body = ['ocean', 'sage', 'terracotta', 'pearl', 'graphite', 'gold'][Math.floor(hash / 3) % 6]
  const nose = width / 2
  return <g className={`car car-${body}`}>
    <rect className="car-shadow" x={-nose + 2} y="-9" width={width} height="22" rx="8" />
    {[-nose + 6, nose - 11].map(x => <g key={x}>
      <rect className="car-tire" x={x} y="-12" width="7" height="5" rx="2" />
      <rect className="car-tire" x={x} y="7" width="7" height="5" rx="2" />
    </g>)}
    <rect className="car-body" x={-nose} y="-10" width={width} height="20" rx={hash % 3 === 1 ? 5 : 8} />
    <path className="car-glass" d={`M${-nose + 8} -7H${nose - 8}L${nose - 5} -4V4L${nose - 8} 7H${-nose + 8}L${-nose + 5} 4V-4Z`} />
    <rect className="car-roof" x={-nose + 10} y="-5.5" width={width - 22} height="11" rx="2" />
    <path className="car-sheen" d={`M${-nose + 6} -8H${nose - 6}`} />
    <path className="car-headlights" d={`M${nose - 2} -5v2m0 6v2`} />
    <path className={brakes ? 'car-brakes on' : 'car-brakes'} d={`M${-nose + 2} -5v2m0 6v2`} />
  </g>
}

function MovingCar({ trip, reduce, finish }: { trip: Trip; reduce: boolean; finish: (id: number) => void }) {
  const { x, y, rotation } = bayOf(trip.next.space_id)
  if (reduce) {
    return <g transform={`translate(${x} ${y}) rotate(${rotation})`}>
      <motion.g initial={{ opacity: trip.arrival ? 0 : 1 }} animate={{ opacity: trip.arrival ? 1 : 0 }}
        transition={{ duration: 0.2 }} onAnimationComplete={() => finish(trip.id)}>
        <Car vehicle={trip.vehicle} brakes={!trip.arrival} />
      </motion.g>
    </g>
  }

  const position = trip.arrival ? {
    x: [62, 144, x - 24, x, x],
    y: [lane, lane, lane, lane + (y < lane ? -12 : 12), y],
    rotate: [0, 0, 0, rotation, rotation],
    opacity: [0, 1, 1, 1, 1],
  } : {
    x: [x, x, x + 20, 964, 1032],
    y: [y, lane + (y < lane ? -12 : 12), lane, lane, lane],
    rotate: [rotation, rotation, 0, 0, 0],
    opacity: [1, 1, 1, 1, 0],
  }
  const times = trip.arrival ? [0, 0.16, 0.62, 0.79, 1] : [0, 0.23, 0.39, 0.88, 1]
  return <motion.g style={{ transformOrigin: '0 0' }}
    initial={{ x: position.x[0], y: position.y[0], rotate: position.rotate[0], opacity: position.opacity[0] }}
    animate={position} transition={{ duration: trip.duration, times, ease: 'easeInOut' }}
    onAnimationComplete={() => finish(trip.id)}>
    <Car vehicle={trip.vehicle} brakes={!trip.arrival} />
  </motion.g>
}

function Planter({ x, y, width }: { x: number; y: number; width: number }) {
  return <g transform={`translate(${x} ${y})`}>
    <rect className="planter-curb" width={width} height="24" rx="12" />
    <rect className="planter-soil" x="3" y="3" width={width - 6} height="18" rx="9" />
    {Array.from({ length: Math.floor(width / 26) }, (_, index) =>
      <g key={index} transform={`translate(${13 + index * 26} 12)`}>
        <ellipse className="shrub-shadow" cx="2" cy="3" rx="8" ry="7" />
        <circle className="shrub" r="7" />
        <circle className="shrub-light" cx="-2" cy="-2" r="4" />
      </g>)}
  </g>
}

function Gate({ x, name, lifted, reduce }: { x: number; name: string; lifted: boolean; reduce: boolean }) {
  return <g transform={`translate(${x} 222)`}>
    <rect className="gate-island" x="-13" y="-40" width="26" height="18" rx="5" />
    <rect className="gate-island" x="-13" y="24" width="26" height="18" rx="5" />
    <rect className="gate-base" x="-6" y="-35" width="12" height="10" rx="3" />
    <g transform="translate(0 -28)">
      <motion.g initial={false} animate={{ rotate: lifted ? -76 : 0 }} style={{ transformOrigin: '0 0' }}
        transition={{ duration: reduce ? 0 : 0.28 }}>
        <path className="gate-arm" d="M0 0v43" />
        <path className="gate-stripe" d="M0 5v35" />
      </motion.g>
    </g>
    <text className="gate-label" textAnchor="middle" y="63">{name}</text>
  </g>
}

export function Lot({ spaces, inspect, mode = 'live' }: { inspect: (space: ParkingSpace) => void; spaces?: ParkingSpace[]; mode?: 'live' | 'simulate' }) {
  const motionState = useLotMotion(spaces)
  const reduce = useReducedMotion() ?? false
  const id = useId()
  const { trip, queue, notice, finishTrip } = motionState
  const drawn = new Map(motionState.spaces.map(space => [space.space_id, space]))
  const queuedArrivals = new Set(queue.filter(queued => queued.arrival).map(queued => queued.next.space_id))
  const title = `lot-${id}`
  return (
    <div className={`lot-scene lot-${mode}`}>
      <div className="map-heading"><strong>ParkPilot Lot</strong><span>Gate A to Gate B</span></div>
      <div className="scene-perspective">
        <svg className="lot-svg" viewBox="0 0 1060 427" role="group" aria-labelledby={title}>
          <title id={title}>Twenty parking bays, with an entry on the left and an exit on the right</title>
          <defs>
            <pattern id={`concrete-${id}`} width="46" height="46" patternUnits="userSpaceOnUse">
              <rect className="paving" width="46" height="46" />
              <path className="paving-joint" d="M0 46V0h46" />
            </pattern>
            <pattern id={`blocked-${id}`} width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(35)">
              <path className="bay-hatch" d="M0 0v7" />
            </pattern>
          </defs>

          <rect className="lot-slab-shadow" x="22" y="37" width="1016" height="363" rx="41" />
          <rect className="lot-slab-edge" x="22" y="31" width="1016" height="359" rx="41" />
          <rect x="22" y="19" width="1016" height="359" rx="41" fill={`url(#concrete-${id})`} />
          <rect className="lot-ground" x="55" y="74" width="950" height="271" rx="25" />
          <rect className="drive-lane" x="38" y="193" width="984" height="58" rx="13" />
          <rect className="lot-seam" x="149" y="91" width="752" height="237" rx="8" />
          <path className="lane-divider" d="M135 222H926" />
          <path className="lane-arrow" d="M272 211h29l-7-7m7 7-7 7m137-7h29l-7-7m7 7-7 7m137-7h29l-7-7m7 7-7 7m137-7h29l-7-7m7 7-7 7" />
          <path className="crossing" d="M142 200v43m8-43v43m8-43v43m744-43v43m8-43v43m8-43v43" />

          <Planter x={95} y={42} width={186} />
          <Planter x={308} y={42} width={443} />
          <Planter x={779} y={42} width={186} />
          <Planter x={95} y={347} width={210} />
          <Planter x={331} y={347} width={396} />
          <Planter x={752} y={347} width={212} />

          {bayIds.map(spaceId => {
            const { x, y, top } = bayOf(spaceId)
            const bay = drawn.get(spaceId)
            const active = trip?.next.space_id === spaceId
            const visual = active ? trip.arrival ? 'incoming' : 'leaving'
              : bay?.status === 'available' && queuedArrivals.has(spaceId) ? 'incoming'
              : bay?.status ?? 'unknown'
            const flash = notice?.next.space_id === spaceId
            return <g key={spaceId} className={`bay bay-${visual}${flash ? ' bay-flash' : ''}`}>
              <title>{spaceId}: {visual}{bay?.vehicle_id ? ` (${bay.vehicle_id})` : ''}</title>
              <rect className="bay-outline" x={x - 32} y={y - 32} width="64" height="64" rx="6" />
              {visual === 'unavailable' && <rect x={x - 30} y={y - 30} width="60" height="60" rx="5" fill={`url(#blocked-${id})`} />}
              <rect className="bay-wheel-stop" x={x - 14} y={top ? y - 25 : y + 20} width="28" height="5" rx="2" />
              <rect className="bay-id-bg" x={x - 16} y={top ? y - 44 : y + 34} width="32" height="15" rx="5" />
              <text className="bay-id" x={x} y={top ? y - 33 : y + 45} textAnchor="middle">{spaceId}</text>
              {(visual === 'available' || visual === 'incoming') &&
                <path className="bay-indicator" d={`M${x - 5} ${y + 5}h10`} />}
            </g>
          })}

          <Gate x={99} name="Entry" lifted={!!trip?.arrival} reduce={reduce} />
          <Gate x={960} name="Exit" lifted={!!trip && !trip.arrival} reduce={reduce} />
          {motionState.spaces.map(space => {
            if (space.status !== 'occupied' || !space.vehicle_id || trip?.next.space_id === space.space_id) return null
            const { x, y, rotation } = bayOf(space.space_id)
            return <g key={space.space_id} transform={`translate(${x} ${y}) rotate(${rotation})`}>
              <Car vehicle={space.vehicle_id} />
            </g>
          })}
          {motionState.spaces.filter(space => space.status === 'occupied' && trip?.next.space_id !== space.space_id).map(space => {
            const { x, y } = bayOf(space.space_id)
            return <rect key={space.space_id} className="bay-hit" x={x - 32} y={y - 32} width="64" height="64" rx="6"
              role="button" tabIndex={0} aria-label={`Inspect ${space.vehicle_id} in ${space.space_id}`}
              onClick={() => inspect(space)} onKeyDown={event => {
                if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); inspect(space) }
              }} />
          })}
          {trip && <MovingCar key={trip.id} trip={trip} reduce={reduce} finish={finishTrip} />}
          {notice && <g transform={`translate(${bayOf(notice.next.space_id).x} ${bayOf(notice.next.space_id).top ? 80 : 261})`}
            className="bay-callout">
            <rect x="-83" y="-16" width="166" height="31" rx="10" />
            <text textAnchor="middle" y="4">{notice.next.space_id} {notice.arrival ? 'arrived' : 'departed'}</text>
          </g>}
        </svg>
      </div>
      <div className="map-legend" aria-label="Bay legend">
        <span><i className="legend-swatch available" />Available</span>
        <span><i className="legend-swatch occupied" />Occupied</span>
        {trip && <span aria-live="polite">{trip.next.space_id} {trip.arrival ? 'incoming' : 'leaving'}</span>}
      </div>
      <ul className="sr-only" aria-label="Parking bay statuses">
        {spaces?.map(space => <li key={space.space_id}>{space.space_id} {space.status} {space.vehicle_id}</li>)}
      </ul>
    </div>
  )
}
