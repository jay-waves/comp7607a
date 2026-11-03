# LoopGuard presentation

Independent Markdown/Slidev deck with React + TypeScript widgets and global Paul Tol Muted CSS tokens. “typstscript” is interpreted as TypeScript. Slidev retains its Vue host; React mounts through `components/ReactDemo.vue`.

Requires Node.js 22+. Frontend commands use npm in this directory; Python continues to use uv at repository root.

```sh
npm ci
npm run dev
npm run typecheck
npm run build
```

Serve `dist/` over HTTP for the HTML presentation. Build uses relative asset paths. Edit `slides.md`, `react/`, and `styles/index.css`; Slidev automatically loads the global stylesheet. No external fonts or APIs are required by this template. The React counter is synthetic and does not implement LoopGuard detection.

Optional PDF: install `playwright-chromium` as a dev dependency and run `npm run export`. HTML is the acceptance target.

Palette reference: https://sronpersonalpages.nl/~pault/ . See AGENTS.md for aliases and authoring constraints.

## GitHub Pages

The demo follows PROPOSAL.md: research question, scope/design, experiments, deliverables/schedule, and references. All experimental targets are labeled as planned, not measured.

`.github/workflows/presentation.yml` checks pull requests and builds/deploys changes on `main`; it also supports manual dispatch on `main`. Only `presentation/dist` is published. Hash routing and relative assets support the repository subpath without server rewrite rules.

One-time repository setup: Settings → Pages → Build and deployment → Source → **GitHub Actions**. The workflow needs Pages enabled and the `github-pages` environment must allow `main`. No custom secret is required. After pushing, the deployment job exposes the actual URL; the expected default URL is https://jay-waves.github.io/comp7607a/ .

The workflow uses GitHub's Pages artifact/OIDC deployment flow: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages . It does not commit generated files or publish trace databases.

The presentation includes three visx charts (policy token use, success/false-stop rates, and cumulative tool calls) with explicitly fabricated data for layout demonstration. They are not experimental results, predictions, or evidence for the exploratory target.
