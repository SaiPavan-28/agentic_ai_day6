# Design: add-api-and-ui

## Context
Exposing the LangGraph incident triage agent over FastAPI and Gradio UI requires uniform response handling and approval workflows.

## Key Decisions
1. **Shared Service Layer**: Implement core business logic in `service_chat` and `service_approve` functions in `app.py`. Both FastAPI route handlers and Gradio callback functions call these shared functions to guarantee identical approval behavior.
2. **Gradio Mounting**: Use `gr.mount_gradio_app(app, ui, path="/")` to combine FastAPI and Gradio into a single ASGI application object `app`.
3. **HTTP 400 for Invalid Approval**: Raise HTTP 400 when `/approve` is called for a thread that is not awaiting approval.

## Alternatives Considered
- Independent Gradio and FastAPI handlers: Rejected to avoid code duplication and divergent approval logic.
