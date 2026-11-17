export type ParkingSpace = {
  space_id: string
  status: 'available' | 'occupied' | 'unavailable'
  vehicle_id: string | null
  last_updated: string
}

export type ParkingEvent = {
  event_id: number
  space_id: string
  event_type: 'SPACE_OCCUPIED' | 'SPACE_AVAILABLE'
  vehicle_id: string
  timestamp: string
}

export type SimulationStatus = { running: boolean }
export type SimulationSpeed = { speed: number }

export type Analytics = {
  capacity: number
  points: { timestamp: string; occupied: number }[]
  hourly: { hour: string; arrivals: number; departures: number }[]
  spaces: { space_id: string; arrivals: number }[]
  total_arrivals: number
  total_departures: number
}

export type Facility = {
  facility_id: string
  first_reference_at: string
  last_reference_at: string
  reference_times: string[]
}

export type Facilities = {
  source: 'uci_parking_birmingham'
  horizon_minutes: 30
  facilities: Facility[]
}

export type LiveFacility = {
  id: string
  name: string
  max_horizon_minutes: number
}

export type LiveForecast = {
  explanation: ForecastExplanation
  facility_id: string
  capacity: number
  arrival_at: string
  observed_at: string
  last_change_at: string
  horizon_minutes: number
  current_occupied: number
  estimated_occupied: number
  estimated_free: number
  model: string
  source: 'live_simulation' | 'simulated_calendar'
}

export type Forecast = {
  explanation: ForecastExplanation
  source: 'uci_parking_birmingham'
  facility_id: string
  horizon_minutes: 30
  model_name: string
  reference_at: string
  target_at: string
  as_of: string
  capacity: number
  current_occupancy: number
  predicted_occupancy: number
  predicted_free_spaces: number
  actual_occupancy: number | null
  actual_free_spaces: number | null
  history: { timestamp: string; occupancy: number }[]
  metrics: { mae: number; rmse: number; r2: number | null }
}

export type ForecastExplanation = {
  inputs: { label: string; value: string }[]
  steps: string[]
  tree_predictions: number[]
  raw_occupied: number
}

export class ApiError extends Error {
  constructor(readonly status: number, detail: string) {
    super(detail)
  }
}

export const apiUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${apiUrl}${path}`, options)
  } catch (error) {
    if (options?.signal?.aborted) throw error
    throw new ApiError(0, 'The parking API is unreachable. Check that FastAPI is running.')
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new ApiError(
      response.status,
      typeof body?.detail === 'string' ? body.detail : `The API returned HTTP ${response.status}.`,
    )
  }
  return response.json() as Promise<T>
}

export const getSpaces = (signal: AbortSignal): Promise<ParkingSpace[]> =>
  request('/parking-spaces', { signal })

export const getEvents = (signal: AbortSignal): Promise<ParkingEvent[]> =>
  request('/events?limit=50', { signal })

export const getStatus = (signal: AbortSignal): Promise<SimulationStatus> =>
  request('/simulation/status', { signal })

export const getSpeed = (signal: AbortSignal): Promise<SimulationSpeed> =>
  request('/simulation/speed', { signal })

export const getAnalytics = (signal: AbortSignal): Promise<Analytics> =>
  request('/analytics', { signal })

export const getLiveFacilities = (signal: AbortSignal): Promise<LiveFacility[]> =>
  request('/live-forecast/facilities', { signal })

export const getLiveForecast = (facility: string, arrivalAt: string, signal: AbortSignal): Promise<LiveForecast> =>
  request(`/live-forecast/${encodeURIComponent(facility)}?${new URLSearchParams({ arrival_at: arrivalAt })}`, { signal })

export const getFacilities = (signal: AbortSignal): Promise<Facilities> =>
  request('/forecast/facilities', { signal })

export const getForecast = (
  params: { facility_id: string; reference_at?: string; as_of?: string },
  signal?: AbortSignal,
): Promise<Forecast> => {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => { if (value) query.set(key, value) })
  return request(`/forecast?${query}`, { signal })
}

export const setRunning = (running: boolean): Promise<SimulationStatus> =>
  request(`/simulation/${running ? 'start' : 'stop'}`, { method: 'POST' })

export const sendEvent = (type: 'arrival' | 'departure'): Promise<ParkingEvent> =>
  request(`/simulation/${type}`, { method: 'POST' })

export const setSpeed = (speed: number): Promise<SimulationSpeed> =>
  request('/simulation/speed', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ speed }),
  })
