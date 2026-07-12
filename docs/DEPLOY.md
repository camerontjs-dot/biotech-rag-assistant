# Deploying the demo on GitHub Pages (private repo)

Goal: keep the repo **private**, publish the static demo (`docs/index.html`) so you can share a
link, and let a specific person see the code if you choose. Here's how, and the one caveat.

## The access reality (read first)

- On **Free/Pro** plans, a GitHub Pages **site is public** even when its source repo is private.
  (Access-controlled "private Pages" requires GitHub Enterprise Cloud.)
- That's fine here: the demo is **100% synthetic** and client-side — no secrets, no client data,
  no backend. So: **repo private, demo URL public (share it with anyone), code visible only to
  collaborators.**
- To let someone see the **code**, add them as a repo collaborator
  (repo → Settings → Collaborators → Add people). That's the normal way to share a private repo.

## One-time setup

This workbench is already a git repo with the demo committed under `docs/`. Create a private
GitHub repo and push:

```bash
# from the workbench root
gh repo create biotech-rag-assistant --private --source=. --remote=origin --push
# (or: create the private repo in the web UI, then)
#   git remote add origin git@github.com:<you>/biotech-rag-assistant.git && git push -u origin main
```

Enable Pages (web UI): repo → **Settings → Pages → Build and deployment → Source: Deploy from a
branch → Branch: `main`, folder: `/docs` → Save**. After ~1 minute the site is live at:

```
https://<your-username>.github.io/biotech-rag-assistant/
```

That's the link you share with Sameer. `index.html` is the landing page.

> Note: serving `/docs` also exposes the other files in this folder (`api-transport.md`, the
> baseline notes) as public URLs. They're non-sensitive synthetic-system docs, so this is
> harmless. If you want **only** the demo public, see the alternative below.

## Keeping the demo faithful before each push

The static demo must not drift from the Python core. After any corpus or retrieval change:

```bash
python scripts/build_pages_demo.py    # re-exports corpus-data.json + asserts JS==Python (40/40)
git add docs/ && git commit -m "demo: refresh static Pages data" && git push
```

## Alternative — publish only the demo (optional, cleaner)

If you'd rather not expose the other `docs/*.md`, deploy via GitHub Actions from a dedicated
folder instead of branch/`docs`: move `index.html`, `retrieval.js`, `corpus-data.json`,
`.nojekyll` into a `site/` folder and add a workflow that uploads only `site/` with
`actions/upload-pages-artifact` + `actions/deploy-pages`. Pages source → "GitHub Actions". This
publishes exactly the demo, nothing else. (More setup; the `/docs` path above is the simplest and
is what most people do.)

## What this is

Not a validated GxP/quality system. The demo helps find and cite approved documents and refuses
when unsupported; it does not certify compliance or make regulated decisions.
