# Proposal: add-api-and-ui

## Summary
Implement FastAPI REST API endpoints (`POST /chat`, `POST /approve`) and a Gradio web interface mounted at `/` in `app.py`, sharing a single service layer logic (`service_chat` and `service_approve`).

## Why
Engineers and external systems need REST and interactive UI interfaces to run incident triage and approve or reject sensitive escalation actions.

## What
- Shared service layer functions `service_chat` and `service_approve`.
- REST endpoint `POST /chat` returning `COMPLETED` or `AWAITING_APPROVAL`.
- REST endpoint `POST /approve` processing approval or rejection, and returning HTTP 400 when no approval is pending.
- Gradio Blocks UI mounted at `/` with Thread ID input, incident prompt, status state label, agent log, and approval/rejection controls.
- Integration unit tests in `tests/test_api.py`.

## Affected Capabilities
- `triage-api` (ADDED)
- `triage-ui` (ADDED)

## Rollback
Remove `app.py` REST routes and Gradio mounting.
