# Proposal: add-triage-agent-core

## Summary
Implement the core read-only triage agent in `agent.py` using LangGraph, Gemini LLM, safe tools (`query_service_health`, `search_remediation_runbooks`), and state persistence.

## Why
The agent must investigate reported incidents by checking service health before querying internal runbooks, maintaining state across messages.

## What
- LangGraph graph definition in `agent.py` with `agent` node and `safe_tools` node.
- Safe read-only tools: `query_service_health` and `search_remediation_runbooks`.
- Content normalization helper `extract_text`.
- Connection pooling with `psycopg_pool.ConnectionPool` and state checkpointer using `PostgresSaver`.
- `get_agent_app()` factory returning compiled workflow app.

## Affected Capabilities
- `triage-agent` (ADDED)

## Rollback
Remove `agent.py` and associated test cases in `tests/test_agent.py`.
