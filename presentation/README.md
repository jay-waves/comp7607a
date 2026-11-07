# LoopGuard presentation

Independent reveal.js + React + TypeScript deck, built with Vite. Markdown supplies prose, equations and comparison tables; Pele renders local Mermaid diagrams. Global CSS uses Paul Tol Muted palette tokens. No Vue or Slidev is required.

Requires Node.js 22.12+ (or a newer supported Node release). Use npm here; Python tooling at the repository root continues to use uv.

```sh
npm ci
npm run dev
npm run typecheck
npm run build
npm run preview
```

Serve dist/ over HTTP. Relative asset paths and reveal.js hash navigation support GitHub Pages repository hosting. No external fonts or runtime APIs are required. For PDF, use reveal.js print mode (?print-pdf) and browser Print to PDF.

## Authoring

Edit `slides.md` for prose, HTML formula notation, tables, `---` page separators and `Notes:` speaker notes. `react/main.tsx` assembles the deck through the official @revealjs/react components and mounts Mermaid slides through Pele. `styles/index.css` owns typography, spacing, palette aliases and the editorial layout.

The 23-slide English deck follows the current proposal: research objective → implemented monitor → six-task sandbox → two-stage live evaluation → SQL/MaxSAT extensions → status and limitations. It includes the shared-budget objective, repetition criterion, total-cost accounting and task-defined progress notation. The 126-run figure is a derived planning count (6 tasks × 3 repetitions × 7 conditions), not completed experiments; development and calibration are additional.

`PROPOSAL.md` takes precedence over the earlier stopping-policy protocol retained in `experiments/README.md`. Replay is presented as diagnostic preparation, not evidence of outcomes after effort changes or restart. The deck distinguishes implemented, mock-tested, planned and unmeasured work. It contains no fabricated performance charts or provider price comparisons. Equations are explanatory notation, not newly implemented algorithms. Sources and interpretation caveats are recorded in speaker notes.

## GitHub Pages

.github/workflows/presentation.yml installs locked dependencies, typechecks and builds PRs. On main it publishes only presentation/dist through the Pages artifact/OIDC deployment flow. Manual dispatch is supported on main.

One-time setup: repository Settings → Pages → Build and deployment → Source → GitHub Actions. The github-pages environment must allow main. No custom secret is needed. Expected default URL: https://jay-waves.github.io/comp7607a/ . Actual deployment status and URL are reported by Actions.

## References

- React bindings: https://revealjs.com/react/
- Palette: https://sronpersonalpages.nl/~pault/
- Pages: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages

Typography uses Georgia throughout, with Times New Roman/serif fallbacks when Georgia is unavailable. Candidate harnesses represent future adapter validation, not current support.

## Diagrams

Use one fenced mermaid block per diagram slide, with a heading and optional Notes:. react/MermaidDiagram.tsx mounts Pele SVGs and cleans up on unmount. Only flowchart and sequence renderers are registered. All diagram content is authored locally; no CDN or external rendering service is needed. The global .diagram CSS maps Pele variables to existing palette and Georgia aliases. Keep the measured font and rendered font consistent.

## Single-file distribution

Run `npm run build:single` to generate `dist-single/index.html`. JavaScript, CSS, diagrams, Markdown and chart data are bundled into that HTML, including the lazy Pele module. Send this file directly; it can be opened with file:// without a local server. External reference links still require a network connection, and Georgia depends on the recipient's installed fonts (serif fallbacks apply). The normal Pages build stays in dist/.

Navigation uses a compact React control with previous / page count / next on one line; keyboard navigation remains available.

Tagged releases also build and attach loopguard-presentation.html to the GitHub Release after Python and frontend validation. Its SHA-256 checksum is included in SHA256SUMS.
