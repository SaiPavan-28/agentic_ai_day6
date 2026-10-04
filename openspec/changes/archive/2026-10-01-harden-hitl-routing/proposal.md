# Proposal: harden-hitl-routing

## Summary
Harden the HITL tool routing logic so that if ANY tool call in a model message is sensitive, the entire message is routed to `sensitive_tools` and interrupted for human approval.

## Why
Inspect only the first tool call in a message creates a safety vulnerability when LLMs generate parallel or mixed tool calls (e.g. `[query_service_health, escalate_ticket]`), which would bypass human approval.

## What
- Update `route_tools` in `agent.py` to check `any(tc["name"] == "escalate_ticket" for tc in tool_calls)`.
- Ensure rejection creates a `ToolMessage` for EVERY tool call in the message.
- Update `service_chat` and `service_approve` in `app.py` to correctly handle multi-call pending actions.
- Add regression tests in `tests/test_hitl.py` covering mixed tool calls and multi-call rejection.

## Affected Capabilities
- `hitl-approval` (MODIFIED)

## Rollback
Revert `route_tools` to check only the first tool call.
