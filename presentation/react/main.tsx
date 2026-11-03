import { createRoot } from 'react-dom/client'
import { Deck, Markdown, Slide } from '@revealjs/react'
import 'reveal.js/reveal.css'
import '../styles/index.css'
import content from '../slides.md?raw'
import { ObservationDemo } from './ObservationDemo'
import { ExperimentCharts } from './ExperimentCharts'

// Markdown owns prose; explicit markers place React widgets without raw HTML mounting.
const pages = content.trim().split(/^---\s*$/m)
const kinds = ['tokens', 'quality', 'timeline'] as const

function Presentation() {
  return <Deck config={{ width: 980, height: 552, hash: true, center: false, transition: 'none', slideNumber: true }}>
    {pages.map((page, index) => {
      const marker = page.match(/<!-- widget: (observation|tokens|quality|timeline) -->/)
      if (!marker) return <Markdown key={index}>{page}</Markdown>
      const title = page.match(/^# (.+)$/m)?.[1] ?? 'Demo'
      const kind = kinds.find(value => value === marker[1])
      return <Slide key={index} notes={page.split('Notes:')[1]?.trim()}>
        <h1>{title}</h1>
        {kind ? <ExperimentCharts kind={kind} /> : <ObservationDemo />}
      </Slide>
    })}
  </Deck>
}

createRoot(document.getElementById('root')!).render(<Presentation />)
