# Design: add-hitl-escalation

## Context
Sensitive actions like opening a critical ticket or paging an on-call team require human oversight before proceeding.

## Key Decisions
1. **LangGraph Interruption**: Use `interrupt_before=["sensitive_tools"]` to pause execution before the `sensitive_tools` node runs.
2. **Rejection Handling**: Rejection injects `ToolMessage(content="Rejected by engineer: <reason>")` using `app.update_state(..., as_node="sensitive_tools")` so the agent receives the feedback and continues reasoning without running the tool.
3. **Persistence**: The thread checkpointer preserves the `AWAITING_APPROVAL` state across process restarts.

## Alternatives Considered
- Webhook callbacks: Rejected in favor of LangGraph native state graph checkpointer interrupts.
