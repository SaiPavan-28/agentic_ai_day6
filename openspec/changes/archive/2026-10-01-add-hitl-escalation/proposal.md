# Proposal: add-hitl-escalation

## Summary
Add Human-in-the-Loop (HITL) approval gating for sensitive actions (e.g. `escalate_ticket`) using LangGraph interrupts.

## Why
Automated ticket creation and paging can cause unintended caller disruption or false alarm escalations. Sensitive actions must require explicit human approval before execution.

## What
- Mark `escalate_ticket` as a sensitive tool.
- Route sensitive tool calls to a `sensitive_tools` node.
- Compile graph with `interrupt_before=["sensitive_tools"]`.
- Handle approval (resuming graph) and rejection (injecting `ToolMessage` with rejection reason).
- Unit tests in `tests/test_hitl.py` verifying pause, approval, rejection, and restart persistence.

## Affected Capabilities
- `hitl-approval` (ADDED)

## Rollback
Remove `sensitive_tools` node and `interrupt_before` setting from `agent.py`.
