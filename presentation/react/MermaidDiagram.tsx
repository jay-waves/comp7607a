import { useEffect, useRef } from 'react'
import { mount, register } from 'pele/core'
import flowchart from 'pele/diagrams/flowchart'
import sequence from 'pele/diagrams/sequence'

register(flowchart, sequence)

export function MermaidDiagram({ source }: { source: string }) {
  const host = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!host.current) return
    // Only repository-authored Mermaid is rendered; Pele handles SVG generation.
    const diagram = mount(host.current, source, {
      maxWidth: 900,
      autoDirection: false,
      fontSize: 20,
      padding: 20,
      zoom: false,
    })
    return () => diagram.destroy()
  }, [source])
  return <figure className="diagram-figure">
    <div ref={host} className="diagram" />
    <details><summary>View Mermaid source</summary><pre>{source}</pre></details>
  </figure>
}
