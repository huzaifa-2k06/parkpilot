import { useId } from 'react'

export function ForecastCapacityMap({ capacity, occupied }: { capacity: number; occupied: number }) {
  const id = useId()
  const columns = Math.ceil(capacity / 2)
  const width = Math.max(400, columns * 54 + 80)
  return <figure className="forecast-capacity">
    <figcaption>
      <strong>Estimated parking capacity at arrival</strong>
      <span>Illustrative placement of {capacity - occupied} free and {occupied} occupied spaces.
        Individual bay availability will be known at arrival.</span>
    </figcaption>
    <svg viewBox={`0 0 ${width} 228`} role="img" aria-labelledby={id}>
      <title id={id}>Forecast capacity diagram with {capacity - occupied} estimated free and {occupied} estimated occupied spaces</title>
      <rect className="forecast-ground" x="8" y="8" width={width - 16} height="212" rx="18" />
      <path className="forecast-lane" d={`M22 114H${width - 22}`} />
      {Array.from({ length: capacity }, (_, index) => {
        const x = 40 + index % columns * 54
        const y = index < columns ? 30 : 144
        const taken = index < occupied
        return <g key={index} className={taken ? 'capacity-occupied' : 'capacity-free'}>
          <rect className="forecast-bay" x={x} y={y} width="44" height="54" rx="5" />
          {taken ? <g>
            <rect className="forecast-car" x={x + 10} y={y + 6} width="24" height="35" rx="7" />
            <path className="forecast-window" d={`M${x + 14} ${y + 15}h16m-16 17h16`} />
          </g> : <text x={x + 22} y={y + 32} textAnchor="middle">Free</text>}
        </g>
      })}
    </svg>
    <div className="capacity-key"><span>{capacity - occupied} estimated free</span><span>{occupied} estimated occupied</span></div>
  </figure>
}
