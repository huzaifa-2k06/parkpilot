import { useId } from 'react'
import type { ForecastExplanation } from '../api/parking'

export function ForecastProcess({ explanation, model, occupied, capacity }: {
  explanation: ForecastExplanation
  model: string
  occupied: number
  capacity: number
}) {
  const id = useId()
  const trees = explanation.tree_predictions
  const maximum = Math.max(1, ...trees)
  const minimum = Math.min(...trees)
  return <details className="forecast-process" open>
    <summary>How this forecast works</summary>
    <p className="process-caption">Computed for this selection using {model}.</p>
    <div className="process-flow">
      <section aria-labelledby={id + '-inputs'}>
        <h4 id={id + '-inputs'}>Inputs</h4>
        <dl className="process-inputs">
          {explanation.inputs.map(input => <div key={input.label}>
            <dt>{input.label}</dt><dd>{input.value}</dd>
          </div>)}
        </dl>
      </section>
      <section aria-labelledby={id + '-method'}>
        <h4 id={id + '-method'}>{model}</h4>
        <ol>{explanation.steps.map(step => <li key={step}>{step}</li>)}</ol>
      </section>
      <section aria-labelledby={id + '-output'}>
        <h4 id={id + '-output'}>Estimated capacity</h4>
        <strong className="process-number">{(capacity - occupied).toFixed(1)} free</strong>
        <p>{capacity} total − {occupied.toFixed(1)} occupied</p>
        <meter min={0} max={capacity} value={occupied} aria-label="Estimated occupied capacity" />
      </section>
    </div>
    {trees.length > 0 && <div className="tree-votes">
      <h4>Inside the forest</h4>
      <p>Each bar is one tree’s prediction for this arrival. Their average is {explanation.raw_occupied.toFixed(2)} occupied spaces.</p>
      <svg viewBox="0 0 640 130" role="img" aria-labelledby={id + '-trees'}>
        <title id={id + '-trees'}>{trees.length} tree predictions ranging from {minimum.toFixed(2)} to {maximum.toFixed(2)} occupied spaces</title>
        {trees.map((value, index) => <rect key={index}
          x={index * 640 / trees.length} y={120 - Math.max(0, value) / maximum * 110}
          width={Math.max(1, 640 / trees.length - 1)} height={Math.max(0, value) / maximum * 110}>
          <title>Tree {index + 1}: {value.toFixed(2)} occupied</title>
        </rect>)}
        <line x1="0" x2="640" y1={120 - explanation.raw_occupied / maximum * 110}
          y2={120 - explanation.raw_occupied / maximum * 110} />
      </svg>
      <p className="process-caption">Tree estimates range from {minimum.toFixed(2)} to {maximum.toFixed(2)} occupied.
        Dashed line shows the average.</p>
      <details><summary>Read individual tree predictions</summary>
        <div className="tree-table"><table>
          <caption>Occupancy estimates before the final capacity bound</caption>
          <thead><tr><th>Tree</th><th>Occupied spaces</th></tr></thead>
          <tbody>{trees.map((value, index) => <tr key={index}>
            <td>{index + 1}</td><td>{value.toFixed(2)}</td>
          </tr>)}</tbody>
        </table></div>
      </details>
    </div>}
  </details>
}
