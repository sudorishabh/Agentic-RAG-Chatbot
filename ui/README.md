# Chatbot UI

A standalone HTML/CSS/JS front-end for the Agentic RAG Chatbot API. No build
step and no dependencies — just static files that talk to the Python API.

## Run

1. Start the API:

   ```
   uvicorn app.main:app --reload
   ```

2. Open the UI. Either:
   - double-click `ui/index.html` (opens as `file://`), or
   - serve the folder, e.g. `python -m http.server 5500 --directory ui` and
     visit `http://localhost:5500`.

The status dot in the top bar turns **green** when the API `/health` check
succeeds.

## Settings (⚙)

- **API base URL** — where the UI sends requests. Default `http://localhost:8000`.
  Saved in `localStorage`.
- **Top-K** — optional override for how many chunks are retrieved per question
  (sent as `top_k`). Blank uses the server default.

Use 🗑 to clear the conversation and start a fresh session.

## CORS

A browser blocks cross-origin requests by default, so the API enables CORS via
the `cors_allow_origins` setting (comma-separated origins, default `*`). To lock
it down, set it in `.env`, e.g.:

```
CORS_ALLOW_ORIGINS=http://localhost:5500
```

## Endpoints used

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Connection status indicator |
| `POST /chat` | Streamed answer (SSE: `token` / `sources` / `done`) |
| `POST /chat/feedback` | Thumbs up/down + clicked citations |

## Files

- `index.html` — markup / layout
- `styles.css` — theme and layout styles
- `app.js` — config, streaming, citation + feedback rendering, settings
