import { lazy, Suspense, useRef, useState } from 'react'
import type { RevealApi } from 'reveal.js'
import { createRoot } from 'react-dom/client'
import { Deck, Markdown, Slide } from '@revealjs/react'
import 'reveal.js/reveal.css'
import '../styles/index.css'
import content from '../slides.md?raw'
const MermaidDiagram = lazy(() => import('./MermaidDiagram').then(module => ({ default: module.MermaidDiagram })))
import { DecisionComparison } from './DecisionComparison'
import { ObservationDemo } from './ObservationDemo'
import { ExperimentCharts } from './ExperimentCharts'

// Markdown owns prose; explicit markers place React widgets without raw HTML mounting.
const pages = content.trim().split(/^---\s*$/m)
const kinds = ['tokens', 'quality', 'timeline'] as const

function Presentation() {
  const deck = useRef<RevealApi | null>(null)
  const [current, setCurrent] = useState(1)
  return <><Deck deckRef={deck} onReady={api => setCurrent(api.getIndices().h + 1)} onSlideChange={() => setCurrent((deck.current?.getIndices().h ?? 0) + 1)} config={{ width: 980, height: 552, hash: true, center: false, transition: 'none', slideNumber: false, controls: false }}>
    {pages.map((page, index) => {
      const marker = page.match(/<!-- widget: (observation|decision|tokens|quality|timeline) -->/)
      const diagram = page.match(/```mermaid\n([\s\S]*?)```/)
      if (!marker && !diagram) return <Markdown key={index}>{page}</Markdown>
      const title = page.match(/^# (.+)$/m)?.[1] ?? 'Demo'
      const kind = kinds.find(value => value === marker?.[1])
      return <Slide key={index} notes={page.split('Notes:')[1]?.trim()}>
        <h1>{title}</h1>
        {diagram ? <Suspense fallback={<p role="status">Loading diagram…</p>}><MermaidDiagram source={diagram[1].trim()} /></Suspense> : marker?.[1] === 'decision' ? <DecisionComparison /> : kind ? <ExperimentCharts kind={kind} /> : <ObservationDemo />}
      </Slide>
    })}
  </Deck>
    <nav className="deck-navigation" aria-label="Slide navigation">
      <button aria-label="Previous slide" disabled={current === 1} onClick={() => deck.current?.prev()}>
        <svg viewBox="0 0 16 16" aria-hidden="true"><path d="m10 3-5 5 5 5" /></svg>
      </button>
      <output aria-label="Current slide" aria-live="polite">{current}<span> / {pages.length}</span></output>
      <button aria-label="Next slide" disabled={current === pages.length} onClick={() => deck.current?.next()}>
        <svg viewBox="0 0 16 16" aria-hidden="true"><path d="m6 3 5 5-5 5" /></svg>
      </button>
    </nav>
  </>
}

createRoot(document.getElementById('root')!).render(<Presentation />)
