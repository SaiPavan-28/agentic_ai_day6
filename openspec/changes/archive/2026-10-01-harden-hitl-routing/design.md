# Design: harden-hitl-routing

## Context
When an LLM produces a parallel tool call batch containing both safe tools and sensitive tools, evaluating only `tool_calls[0]` allows sensitive tool calls at index 1 or later to execute without approval.

## Key Decisions
1. **ANY-based Routing**: `route_tools` evaluates `any(tc["name"] in SENSITIVE_TOOLS for tc in tool_calls)` and routes the entire message to `sensitive_tools` node if true.
2. **Complete ToolMessage Rejection**: On rejection, `service_approve` generates a `ToolMessage` for *every* tool call ID in `last_msg.tool_calls` so no dangling unhandled tool calls remain in the LangGraph state graph.

## Alternatives Considered
- Disabling parallel tool calling in LLM settings: Rejected in favor of robust graph-level tool routing security.
