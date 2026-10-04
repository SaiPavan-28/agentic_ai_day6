# Tasks: add-triage-agent-core

- [x] Create `agent.py` with `AgentState`, system prompt, and `get_agent_app()` graph
- [x] Implement safe tools `query_service_health` and `search_remediation_runbooks`
- [x] Implement `extract_text` helper function for content normalization
- [x] Support `PostgresSaver` checkpointer and fallback test checkpointer
- [x] Create unit tests in `tests/test_agent.py` verifying health-first behavior and persistence
