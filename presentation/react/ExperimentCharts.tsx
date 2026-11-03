import { Bar, LinePath } from '@visx/shape'
import { scaleBand, scaleLinear } from '@visx/scale'

// Fabricated layout fixtures, not observations or predictions from LoopGuard.
const policies = [
  { name: 'A · Budget', tokens: 40, success: 92, falseStops: 0, color: 'var(--color-series-budget)' },
  { name: 'B · Rules', tokens: 26, success: 83, falseStops: 12, color: 'var(--color-series-rules)' },
  { name: 'C · Judge', tokens: 31, success: 90, falseStops: 4, color: 'var(--color-series-judge)' },
]
const trajectories = [
  [0, 6, 12, 18, 24, 30, 36],
  [0, 6, 12, 15, 15, 15, 15],
  [0, 6, 12, 18, 21, 21, 21],
]
const left = 65, top = 25, width = 740, height = 235
const xBand = scaleBand<string>({ domain: policies.map(d => d.name), range: [0, width], padding: 0.4 })

function Grid({ max, unit }: { max: number; unit: string }) {
  const y = scaleLinear({ domain: [0, max], range: [height, 0] })
  return <>{[0, 1, 2, 3, 4].map(i => {
    const value = i * max / 4
    return <g key={i}>
      <line x1={0} x2={width} y1={y(value)} y2={y(value)} className="chart-grid" />
      <text x={-10} y={y(value) + 5} textAnchor="end">{value}</text>
    </g>
  })}<text x={0} y={-10}>{unit}</text></>
}

export function ExperimentCharts({ kind }: { kind: 'tokens' | 'quality' | 'timeline' }) {
  const max = kind === 'quality' ? 100 : 40
  const y = scaleLinear({ domain: [0, max], range: [height, 0] })
  const xTime = scaleLinear({ domain: [0, 6], range: [0, width] })
  const title = kind === 'tokens' ? 'Illustrative median token use' : kind === 'quality' ? 'Illustrative success and false stops' : 'Illustrative cumulative tool calls'
  return <figure className="experiment-chart">
    <figcaption className="simulation-label">模拟数据 / FABRICATED DATA — layout demo only; no experiments run</figcaption>
    <svg viewBox="0 0 860 320" role="img" aria-label={title}>
      <title>{title} — fabricated data, not experimental results</title>
      <g transform={`translate(${left},${top})`}>
        <Grid max={max} unit={kind === 'tokens' ? 'thousand tokens' : kind === 'quality' ? 'percent (%)' : 'tool calls'} />
        {kind === 'timeline' ? trajectories.map((values, index) => <g key={index}>
          <LinePath data={values.map((value, step) => ({ value, step }))} x={d => xTime(d.step)} y={d => y(d.value)} stroke={policies[index].color} strokeWidth={3} strokeDasharray={index === 1 ? '8 5' : index === 2 ? '3 4' : undefined} />
          {values.map((value, step) => <circle key={step} cx={xTime(step)} cy={y(value)} r={4} fill={policies[index].color} />)}
        </g>) : policies.map(d => {
          const x = xBand(d.name) ?? 0
          const bw = xBand.bandwidth()
          return <g key={d.name}>
            <Bar x={x} y={y(kind === 'tokens' ? d.tokens : d.success)} width={kind === 'tokens' ? bw : bw / 2 - 4} height={height - y(kind === 'tokens' ? d.tokens : d.success)} fill={d.color} />
            <text x={x + bw / 2} y={y(kind === 'tokens' ? d.tokens : d.success) - 8} textAnchor="middle">{kind === 'tokens' ? `${d.tokens}k` : `${d.success}% success`}</text>
            {kind === 'quality' && <><Bar x={x + bw / 2 + 4} y={y(d.falseStops)} width={bw / 2 - 4} height={height - y(d.falseStops)} fill="var(--color-series-false-stop)" /><text x={x + bw / 2 + 8} y={y(d.falseStops) - 8}>{d.falseStops}%</text></>}
            <text x={x + bw / 2} y={height + 27} textAnchor="middle">{d.name}</text>
          </g>
        })}
        {kind === 'timeline' && <>{[0, 1, 2, 3, 4, 5, 6].map(step => <text key={step} x={xTime(step)} y={height + 25} textAnchor="middle">{step}</text>)}<text x={width / 2} y={height + 53} textAnchor="middle">Elapsed minutes (synthetic)</text></>}
      </g>
    </svg>
    {kind !== 'tokens' && <div className="chart-legend">{policies.map(d => <span key={d.name}><i style={{ background: d.color }} />{d.name}</span>)}{kind === 'quality' && <span><i className="false-stop-key" />False stops</span>}</div>}
    <details><summary>View fabricated source values</summary><table><thead><tr><th>Policy</th><th>{kind === 'tokens' ? 'Tokens (k)' : kind === 'quality' ? 'Success / false stops (%)' : 'Calls at minute 0–6'}</th></tr></thead><tbody>{policies.map((d, i) => <tr key={d.name}><td>{d.name}</td><td>{kind === 'tokens' ? d.tokens : kind === 'quality' ? `${d.success} / ${d.falseStops}` : trajectories[i].join(', ')}</td></tr>)}</tbody></table></details>
  </figure>
}
