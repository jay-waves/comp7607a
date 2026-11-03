import { Bar } from '@visx/shape'
import { scaleLinear } from '@visx/scale'

// Published specifications, not synthetic experiment results. Checked 2026-11-03.
const models = [
  { name: 'Jev 1.14', price: 0.042, context: 64, detail: '32k/question; 262k opt-in', color: 'var(--color-series-budget)', source: 'https://docs.typesafe.ai/models' },
  { name: 'Clef-flash', price: 0.038, context: 24, detail: 'Hosted context; blog specification', color: 'var(--color-series-rules)', source: 'https://blog.cloudflare.com/clef-faster-cheaper-multimodal/' },
  { name: 'Qwen Decision', price: 0, context: 65, detail: 'Free during preview', color: 'var(--color-series-judge)', source: 'https://www.qwencloud.com/models/decision-model-preview' },
]
export function DecisionComparison() {
  const cost = scaleLinear({ domain: [0, 0.05], range: [0, 255] })
  const context = scaleLinear({ domain: [0, 70], range: [0, 255] })
  return <figure className="decision-comparison">
    <figcaption>Published specifications · 3 Nov 2026 · not measured performance</figcaption>
    <svg viewBox="0 0 870 270" role="img" aria-label="Decision API input prices and context windows">
      <title>Input cost in USD per million tokens and default context in thousand tokens</title>
      <text x={180} y={24}>Input · USD / 1M tokens</text><text x={535} y={24}>Default context · k tokens</text>
      {models.map((model, index) => {
        const y = 58 + index * 72
        return <g key={model.name}>
          <text x={0} y={y + 20}>{model.name}</text>
          <Bar x={180} y={y} width={cost(model.price)} height={28} fill={model.color} />
          <text x={190 + cost(model.price)} y={y + 20}>{model.price === 0 ? 'Free*' : `$${model.price}`}</text>
          <Bar x={535} y={y} width={context(model.context)} height={28} fill={model.color} />
          <text x={545 + context(model.context)} y={y + 20}>{model.context}k</text>
        </g>
      })}
    </svg>
    <div className="spec-notes">{models.map(m => <span key={m.name}><a href={m.source}>{m.name}</a>: {m.detail}</span>)}</div>
    <p className="spec-caveat">*Preview pricing may change. Jev output is free; other output charges are not compared. Context limits differ in semantics. LoopGuard sends ≤6 KB of evidence, not full-window inputs.</p>
  </figure>
}
