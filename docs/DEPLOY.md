# Deploying the demo on GitHub Pages

Goal: publish the static demo (`docs/index.html`) from this public repository. The demo is
client-side and uses a synthetic corpus; it has no secrets, client data, or backend.

## Current access boundary

- `camerontjs-dot/biotech-rag-assistant` is public, as is its GitHub Pages site.
- Pages serves the `docs/` folder, so the other files in that folder are public too. Keep
  sensitive material out of the repository; the checked-in corpus and documentation are synthetic.

## Current Pages configuration

The repository is already configured to deploy the committed `docs/` folder from `main`:

- Source branch: `main`
- Source folder: `/docs`
- Site: <https://camerontjs-dot.github.io/biotech-rag-assistant/>

For an equivalent setup in another repository, use **Settings → Pages → Build and deployment →
Source: Deploy from a branch → Branch: `main`, folder: `/docs`**. GitHub then builds the site from
that branch and folder.

`index.html` is the landing page.

> Note: serving `/docs` also exposes the other files in this folder (`api-transport.md`, the
> baseline notes) as public URLs. They're non-sensitive synthetic-system docs, so this is
> harmless. If you want **only** the demo public, see the alternative below.

## Keeping the demo faithful before each push

The static demo must not drift from the Python core. After any corpus or retrieval change:

```bash
python scripts/build_pages_demo.py    # re-exports corpus-data.json + asserts JS==Python (42/42)
git add docs/ && git commit -m "demo: refresh static Pages data" && git push
```

## Alternative — publish only the demo (optional, cleaner)

If a future repository should expose only the demo, deploy via GitHub Actions from a dedicated
folder instead of branch/`docs`: move `index.html`, `retrieval.js`, `corpus-data.json`,
`.nojekyll` into a `site/` folder and add a workflow that uploads only `site/` with
`actions/upload-pages-artifact` + `actions/deploy-pages`. Pages source → "GitHub Actions". This
publishes exactly the demo, nothing else. (More setup; the `/docs` path above is the simplest and
is what most people do.)

## What this is

Not a validated GxP/quality system. The demo helps find and cite approved documents and refuses
when unsupported; it does not certify compliance or make regulated decisions.
