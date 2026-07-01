# Chatbot UI

Dependency-free, no-build front-ends for the Agentic RAG Chatbot API. Two ways
to ship it:

| File | What it is | Use for |
| --- | --- | --- |
| `widget.js` | **Embeddable widget** — one `<script>` tag injects a floating launcher + chat panel, fully CSS-isolated in a Shadow DOM. | Production / **teriin.org (Drupal)** |
| `index.html` + `app.js` + `styles.css` | Standalone full-page chat app (dark theme). | Quick local dev / a dedicated page |

Both speak the same backend contract (see [Endpoints](#endpoints-used)).

## Embeddable widget (recommended for teriin.org)

Drop a single tag onto any page — that's the whole install:

```html
<script
  src="https://chatbot.teriin.org/ui/widget.js"
  data-api-base="https://chatbot.teriin.org"
  data-title="TERI Assistant"></script>
```

| `data-*` attribute | Meaning | Default |
| --- | --- | --- |
| `data-api-base` | Backend origin the widget calls | `http://localhost:8000` |
| `data-title` | Header / launcher label | `TERI Assistant` |
| `data-top-k` | Optional override for chunks retrieved per question | server default |

The widget self-injects a launcher button (bottom-right), a welcome screen with
TERI-relevant suggestion prompts, a **New chat** button, streamed answers,
and citations. All markup and styles live inside a Shadow DOM,
so the host site's CSS can't leak in and the widget's styles can't leak out.
On phones (≤480px) it expands to full screen.

### TERI branding

Theme colors are CSS variables at the top of the `STYLES()` block in
`widget.js` (`--teri-green`, `--teri-green-dark`, etc.). Adjust them to the
confirmed brand hex — the current values are a TERI-green approximation.

### Drupal integration

The widget needs no Drupal module — it's just a static script tag. Pick one:

1. **Block (no code):** create a *Custom Block* of type *Full HTML* (or a Block
   Layout custom block), paste the `<script>` tag, and place it in the *Footer*
   region so it loads site-wide.
2. **Theme template:** add the tag before `</body>` in your theme's
   `html.html.twig` (e.g. `themes/custom/<theme>/templates/html.html.twig`).
3. **Library (cleanest):** copy `widget.js` into your theme/module, declare it
   in `<name>.libraries.yml`, and attach the library globally via
   `<theme>.info.yml` (`libraries: - <name>/chatbot`) or
   `hook_page_attachments()`.

Serve `widget.js` from an origin the browser can reach and make sure the API's
`CORS_ALLOW_ORIGINS` includes `https://teriin.org` (see [CORS](#cors)).

## Standalone page (local dev)

1. Start the API:

   ```
   uvicorn app.main:app --reload
   ```

2. Open the UI. Either:
   - double-click `ui/index.html` (opens as `file://`), or
   - serve the folder, e.g. `python -m http.server 5500 --directory ui` and
     visit `http://localhost:5500`.

   To preview the **widget** instead, open `demo.html` (a mock host page that
   loads `widget.js`).

The status dot turns **green** when the API `/health` check succeeds.

## Settings (⚙)

- **API base URL** — where the UI sends requests. Default `http://localhost:8000`.
  Saved in `localStorage`.
- **Top-K** — optional override for how many chunks are retrieved per question
  (sent as `top_k`). Blank uses the server default.

Use 🗑 to clear the conversation and start a fresh session.

## CORS

A browser blocks cross-origin requests by default, so the API enables CORS via
the `cors_allow_origins` setting (comma-separated origins, default `*`). When
the widget runs on teriin.org but the API is on another origin, that host must
be allowed. Set it in `.env`, e.g.:

```
CORS_ALLOW_ORIGINS=https://teriin.org,https://www.teriin.org,http://localhost:5500
```

## Endpoints used

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Connection status indicator |
| `POST /chat` | Streamed answer (SSE: `token` / `sources` / `done`) |

## Files

- `widget.js` — **embeddable widget**: self-contained launcher + Shadow-DOM panel, streaming, citations (the Drupal drop-in)
- `demo.html` — mock host page that loads `widget.js` for local preview
- `index.html` — standalone page markup / layout
- `styles.css` — standalone page theme and layout styles
- `app.js` — standalone page logic: config, streaming, citation rendering, settings
