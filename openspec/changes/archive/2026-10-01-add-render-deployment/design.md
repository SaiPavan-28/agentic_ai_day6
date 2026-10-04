# Design: add-render-deployment

## Context
Deploying to Render free web service requires dynamic port binding via `$PORT` environment variable and lightweight health check endpoints.

## Key Decisions
1. **Dynamic Port Binding**: Application binds to `$PORT` passed by Render hosting runtime.
2. **Lightweight Health Check**: Endpoint `GET /healthz` returns `{"status": "ok"}` without initializing LLM or DB connections to enable instant readiness checks.
3. **Secret Security**: All sensitive secrets (`GEMINI_API_KEY`, `DATABASE_URL`) are populated strictly via environment variables.

## Alternatives Considered
- Hardcoded port 8000: Rejected because Render dynamically assigns `$PORT`.
