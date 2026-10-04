# Design: add-triage-agent-core

## Context
The core triage agent handles initial incident investigation safely by retrieving health status and matching runbooks.

## Key Decisions
1. **Health-First System Prompt**: Enforce system prompt ordering instructing the agent to inspect service health via `query_service_health` before searching runbooks via `search_remediation_runbooks`.
2. **Safe Tools Loop**: Separate safe read-only tools into a `safe_tools` node.
3. **Checkpointer Support**: Support `PostgresSaver` in production and fallback to `MemorySaver` for isolated unit tests.
4. **Content Normalization**: Provide `extract_text` to normalize strings, dictionary blocks, and lists emitted by models into standard strings.

## Alternatives Considered
- Direct execution inside agent node: Rejected to maintain clean LangGraph state graph tool-calling architecture.
