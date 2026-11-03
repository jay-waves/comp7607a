import { useState } from 'react'

export function ObservationDemo() {
  const [count, setCount] = useState(0)
  return <section className="panel" aria-label="Synthetic observation demo">
    <p className="eyebrow">SYNTHETIC EXAMPLE · REACT</p>
    <h2>Repeated outcomes: {count}</h2>
    <p role="status">{count >= 3 ? 'Warning: repeated effort observed' : 'Observing tool outcomes'}</p>
    <p>This simplified example only counts clicks. It never stops a process.</p>
    <div className="actions">
      <button onClick={() => setCount(c => c + 1)}>Repeat outcome</button>
      <button className="secondary" onClick={() => setCount(0)}>Reset</button>
    </div>
  </section>
}
