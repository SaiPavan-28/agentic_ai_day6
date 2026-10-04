# Tasks: add-hitl-escalation

- [x] Add `escalate_ticket` tool definition in `agent.py`
- [x] Route sensitive tool calls to `sensitive_tools` node
- [x] Compile graph with `interrupt_before=["sensitive_tools"]`
- [x] Implement rejection handling via `update_state(as_node="sensitive_tools")`
- [x] Create unit tests in `tests/test_hitl.py` covering pause, approval, rejection, and restart persistence
