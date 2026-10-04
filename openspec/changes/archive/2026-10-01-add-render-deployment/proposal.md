# Proposal: add-render-deployment

## Summary
Prepare deployment configuration for hosting the agent service on Render's free tier.

## Why
The agent needs to be hostable in a cloud web environment with zero setup cost using environment variable configuration.

## What
- `render.yaml` blueprint defining web service configuration, build command (`pip install -r requirements.txt`), and start command (`uvicorn app:app --host 0.0.0.0 --port $PORT`).
- Health check endpoint `GET /healthz` returning HTTP 200 without external dependencies.
- Git security verification preventing tracking of `.env`.

## Affected Capabilities
- `deployment` (ADDED)

## Rollback
Remove `render.yaml` and `GET /healthz` endpoint.
